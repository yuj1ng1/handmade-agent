import json
import time
from logger_config import logger

class ToolManager:
    def __init__(self):
        self.tool_registry={}

    def register_tool(self,name,func,schema,cacheable=True):#添加工具时的注册
        self.tool_registry[name]={
            "func":func,
            "schema":schema,
            "cacheable":cacheable
        }

    def get_tools(self):#给agent看的说明书
        return (
            [tool["schema"] for tool in self.tool_registry.values()] #依旧列表推导式
            )
    
    def get_tool_info(self,name):
        return self.tool_registry.get(name,{})

    def run_tool(self,item):#工具调用
        tool_info=self.tool_registry.get(item.name)

        if tool_info is None:
            return False,f"查询{item.name}工具失败"
        try:
            args=json.loads(item.arguments)
        except json.JSONDecodeError as e:
            logger.error(
                f"工具参数解析失败 "
                f"name={item.name} "
                f"arguments={item.arguments} "
                f"error={e}"
            )
            return False,f"工具{item.name}的参数格式错误"
        tool_func=tool_info["func"]

        start_time=time.perf_counter()

        try:
            result=tool_func(**args)
        except Exception as e:
            cost_time=time.perf_counter()-start_time
            logger.error(
                f"工具执行失败 "
                f"name={item.name} "
                f"args={args} "
                f"time={cost_time:.2f}s "
                f"error={e}"
            )
            return False,f"工具{item.name}执行失败:{e}"
        
        cost_time=time.perf_counter()-start_time
        logger.info(
        f"工具调用成功 "
        f"name={item.name} "
        f"args={args} "
        f"time={cost_time:.2f}s"
        )

        return True,result