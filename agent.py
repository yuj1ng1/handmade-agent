import json
from logger_config import logger
from pathlib import Path
from memory_store import MemoryStore
from model_client import ModelClient
from config import (
    MAX_AGENT_LOOPS,
    MAX_HISTORY_ROUNDS,
    MAX_TOOL_CALLS,
    MODEL_RETRIES,
    MAX_TOOL_OUTPUT_LENGTH
)
from memory_manager import MemoryManager
from tool_manager import ToolManager

log_path=Path(__file__).parent/"agent.log"

class Agent:
    def __init__(self,client,system_prompt):
        self.system_prompt=system_prompt

        self.history=[]
        self.tool_manager=ToolManager()
        self.memory_path=Path(__file__).parent / "memory.json"

        self.max_loop_round=MAX_AGENT_LOOPS  
        self.max_history_round=MAX_HISTORY_ROUNDS
        self.max_tool_calls=MAX_TOOL_CALLS
        self.max_tool_output_length=MAX_TOOL_OUTPUT_LENGTH
        self.model_retries=MODEL_RETRIES

        self.memory_store=MemoryStore(self.memory_path)

        self.model_client=ModelClient(
            client=client,
            model_name="deepseek-flash",
            retries=self.model_retries
                                      )
        self.memory_manager=MemoryManager(
            model_client=self.model_client,
            memory_store=self.memory_store,
            max_history_round=self.max_history_round,
            max_tool_output_length=self.max_tool_output_length
        )

    def register_tool(self,name,func,schema,cacheable=True): #接受tool_manager中register tool的返回值
        self.tool_manager.register_tool(
            name=name,
            func=func,
            schema=schema,
            cacheable=cacheable
            )

    def get_function_calls(self,response):
        return [item for item in response.output if item.type=="function_call"]

    def handle_tool_call(self,item,tool_cache,tool_call_count,max_tool_calls):
        try:
            args=json.loads(item.arguments)#存入工具参数信息,这里是一个json字符串
            args_key=json.dumps(
                args,
                ensure_ascii=False,
                sort_keys=True
                    )
        except json.JSONDecodeError:
                args_key=item.arguments

        call_key=(item.name,args_key)#存入工具名以及参数信息,元组
        tool_info=self.tool_manager.get_tool_info(item.name)
        cacheable=tool_info.get("cacheable",True)

        if cacheable and (call_key in tool_cache):
            result=tool_cache[call_key]   #toolcache={ call_key:result }
            logger.info(
                        f"命中工具缓存 "
                        f"name={item.name} "
                        f"args={args_key} "
                    )
        elif tool_call_count>=max_tool_calls:
            result=(    
                "本次任务的工具调用次数已达上限，"
                "请停止调用工具，并根据已有信息完成回答。"
                        )
        else:
            tool_call_count+=1
            logger.info(
            f"工具调用计数 "
            f"count={tool_call_count}/{max_tool_calls} "
            f"name={item.name}"
                    )
            success,result=self.tool_manager.run_tool(item)#调用工具
            if cacheable and success:
                tool_cache[call_key]=result

        output_item={
            "type": "function_call_output",
            "call_id": item.call_id,
            "output": str(result)
                }
                    
        return tool_call_count,output_item
        
    def handle_final_answer(self,response,loop_num):
        logger.info(
            f"agent loop完成 round={loop_num} result='final_answer' "
        )
        ans=response.output_text
            
        self.history.append(
        {
        "role":"assistant",
        "content":ans
        }
           )
        return ans 

    
    def get_recent_history(self):   #读取最近5条的用户输入
        recent_indexes=self.memory_manager.get_user_indexs(self.history)#用户输入在history中的索引
        
        if len(recent_indexes)<=self.max_history_round:
            return self.history
        
        trim_index=recent_indexes[-self.max_history_round] #倒着数切
        return self.history[trim_index:]  #从切的地方往后读取
    

    def get_instructions(self):
        instructions=self.system_prompt
        if self.memory_manager.user_memory:
            instructions += f"\n\n长期记忆：\n{self.memory_manager.user_memory}\n"
        if self.memory_manager.conversation_summary:
            instructions += f"\n\n会话摘要：\n{self.memory_manager.conversation_summary}"
        return instructions


    def ask(self,prompt):
        tool_call_count=0
        max_tool_calls=self.max_tool_calls
        tool_cache={}#工具调用缓存

        self.history.append(
            {
            "role":"user",
            "content":prompt
            }
        )
        try:
            self.memory_manager.summarize_history(self.history)  #进行记忆更新
        except Exception as e:
            logger.error(
                f"记忆更新失败 "
                f"error={e}"
            )

        for loop_num in range(1,self.max_loop_round+1):
            logger.info(
                f"agent loop开始 round={loop_num}"
            )
            if tool_call_count>=max_tool_calls:
                available_tools=[]
            else:
                available_tools=self.tool_manager.get_tools()
            try:
                response=self.model_client.call_model(
                    input_data=self.get_recent_history(),
                    instructions=self.get_instructions(),
                    tools=available_tools
                )
            except Exception as e:
                logger.error(
                    f"模型最终调用失败 "
                    f"round={loop_num} "
                    f"error={e}"
                )
                return f"模型调用失败，error={e}"

            function_calls=self.get_function_calls(response=response)

            if not function_calls:
                return self.handle_final_answer(response=response,loop_num=loop_num)
        
            self.history.extend(response.output)

            for item in function_calls:
                tool_call_count,output_item=self.handle_tool_call(
                    item=item,
                    tool_cache=tool_cache,
                    tool_call_count=tool_call_count,
                    max_tool_calls=max_tool_calls
                    )
                self.history.append(output_item)
                
            logger.info(
                f"agent loop完成 round={loop_num} result='continue' "
            )
        logger.warning(
            f"agent已达到最大loop轮数 max_rounds={self.max_loop_round}"
        )
        return f"agent已达到上限"
