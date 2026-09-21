import os
import tools
from dotenv import load_dotenv
from openai import OpenAI
from agent import Agent
from prompts import system_prompt
from tools import *
from tool_registry import tool_registry

load_dotenv()
api_key=os.getenv("DEEPSEEK_API_KEY")
if api_key is None:
    raise ValueError("没有找到可以调用的apikey")

client=OpenAI(
    api_key=api_key,
    base_url="https://api.deepseek.com",
    max_retries=0
)

agent=Agent(client,system_prompt)

for name,info in tool_registry.items():
    agent.register_tool(
        name,
        info["func"],
        info["schema"],
        info.get("cacheable",True)
    )


while True:
    user_input=input("你：")
    if user_input.lower() in ["exit","quit"]:
        print("程序已退出")
        break
    res=agent.ask(user_input)
    print(res)