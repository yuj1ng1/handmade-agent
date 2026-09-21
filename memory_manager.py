

class MemoryManager:
    def __init__(
            self,
            model_client,
            memory_store,
            max_history_round,
            max_tool_output_length
        ):
        self.model_client=model_client
        self.memory_store=memory_store
        self.max_history_round=max_history_round    
        self.max_tool_output_length=max_tool_output_length

        self.user_memory=""
        self.conversation_summary=""
        self.summary_index=0

        self.load_memory()  #在记忆管理这个对象被实例化后立即加载长期记忆以及对话总结

    def save_memory(self):
        self.memory_store.save(
            self.user_memory,
            self.conversation_summary
        )
    
    def load_memory(self):
        memory_data=self.memory_store.load_memory()
        self.user_memory=memory_data.get("user_memory","")
        self.conversation_summary=memory_data.get("conversation_summary","")

    def get_user_indexs(self,history):#获取用户对话在历史中的索引位置
        user_indexes=[]
        for i,item in enumerate(history):
            if isinstance(item,dict) and item.get("role")=="user":
                user_indexes.append(i)
        return user_indexes
    

    def get_summary_boundary(self,history):#获取概括上下文的边界
        user_indexes=self.get_user_indexs(history)  
        if len(user_indexes)<=self.max_history_round: #对话长度还没有超过限制时不产生边界
            return None
        return user_indexes[-self.max_history_round]    #返回列表user_index[-5]给summarizehistory使用
    
    def summarize_history(self,history):  #总结对话形成长期记忆  这里需要传入agent中的history
        boundary=self.get_summary_boundary(history)
        if boundary is None: #对话长度没超时边界的返回值为空，获取边界的函数已经判断
            return
        if boundary<=self.summary_index:
            return 
        
        old_history=history[self.summary_index:boundary]
        memory_text=""
        conversation_text=""
        call_names={}
        
        for item in old_history:
            if isinstance(item,dict):
                role=item.get("role")
                content=item.get("content")
            
                if role and content:
                    conversation_text+=f"{role}:{content}\n"
                if role=="user":
                    memory_text+=f"user:{content}\n"

                if item.get("type")=="function_call_output":
                    call_id=item.get("call_id")
                    output=str(item.get("output",""))
                    tool_name=call_names.get(call_id,"unknown_tool")

                    if(len(output))>self.max_tool_output_length:
                        output=output[:self.max_tool_output_length]+"已截断"
                    if output:
                        conversation_text+= (
                            f"tool:{tool_name}\n"
                            f"output:{output}\n"
                        )

                continue
            if getattr(item,"type",None)=="function_call":
                call_id=getattr(item,"call_id",None)
                tool_name=getattr(item,"name","unknown_tool")
                if call_id:
                    call_names[call_id]=tool_name
        if not memory_text and not conversation_text:
            return 
            
        new_user_memory=self.user_memory
        new_conversation_summary=self.conversation_summary

        if memory_text:
            new_user_memory=self.update_user_memory(memory_text)
        if conversation_text:
            new_conversation_summary=self.summarize_conversation(conversation_text)
        
        self.user_memory=new_user_memory
        self.conversation_summary=new_conversation_summary

        #更新记忆以及已压缩边界索引
        self.summary_index=boundary
        self.save_memory()

    def update_user_memory(self,text):#更新用户记忆
        response=self.model_client.call_model(
            input_data=f"""
                        已有用户记忆：
                        {self.user_memory}

                        新增历史：
                        {text}
                        """,

            instructions="""
                        请更新用户长期记忆。

                        只保留：
                        - 用户姓名或称呼
                        - 用户明确的长期偏好
                        - 用户长期目标
                        - 用户明确要求以后持续遵守的规则

                        不要保留：
                        - 临时天气查询
                        - 临时计算
                        - 一次性的百科问题
                        - 普通寒暄
                        """,
            tools=None
        )
        return response.output_text

    def summarize_conversation(self, text):#概括对话摘要
        response = self.model_client.call_model(
        input_data=  f"""
                    已有会话摘要：
                    {self.conversation_summary}

                    新增历史：
                    {text}
                    """, 
        instructions="""
                    请更新本次会话摘要。

                    保留：
                    - 用户查询过的重要主题
                    - 用户调用过哪些工具
                    - 已经得到的重要结果
                    - 当前对话正在讨论什么

                    不要保留：
                    -对话中的过于细节的数字
                    -对话中的重复内容
                    -普通寒暄

                    压缩重复和无关寒暄。
                    摘要尽量简短
                    """,
        tools=None
    )

        return response.output_text