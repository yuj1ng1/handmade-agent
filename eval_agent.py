import os

from dotenv import load_dotenv
from openai import OpenAI

import tools
from agent import Agent
from tool_registry import tool_registry
from prompts import system_prompt


load_dotenv()

api_key = os.getenv("DEEPSEEK_API_KEY")

client = OpenAI(
    api_key=api_key,
    base_url="https://api.deepseek.com",
    max_retries=0
)


def create_agent():
    agent = Agent(
        client=client,
        system_prompt=system_prompt
    )

    for name, tool_info in tool_registry.items():
        agent.register_tool(
            name=name,
            func=tool_info["func"],
            schema=tool_info["schema"],
            cacheable=tool_info.get(
                "cacheable",
                True
            )
        )

    return agent


def get_called_tools(history):
    called_tools = []

    for item in history:
        if getattr(
            item,
            "type",
            None
        ) == "function_call":
            called_tools.append(
                getattr(
                    item,
                    "name",
                    None
                )
            )

    return called_tools


eval_cases = [
    {
        "question": "现在几点？",
        "expected_tools": ["get_time"]
    },
    {
        "question": "北京今天天气怎么样？",
        "expected_tools": ["get_weather"]
    },
    {
        "question": "23乘以17是多少？",
        "expected_tools": ["calculate"]
    },
    {
        "question": "请查询维基百科，Python编程语言是什么？",
        "expected_tools": ["search_wiki"]
    },
    {
        "question": "你好",
        "expected_tools": []
    },
    {
        "question": "写一个简单的Python for循环示例",
        "expected_tools": []
    },
    {
        "question": "帮我看看今天OpenAI有什么最新消息",
        "expected_tools": ["get_time", "web_search"]
    }
]


passed = 0

for case in eval_cases:
    agent = create_agent()

    answer = agent.ask(
        case["question"]
    )

    called_tools = get_called_tools(
        agent.history
    )

    expected_tools = case["expected_tools"]

    success = all(
        tool in called_tools
        for tool in expected_tools
    )

    if expected_tools == []:
        success = len(called_tools) == 0

    if success:
        passed += 1
        result = "PASS"
    else:
        result = "FAIL"

    print("问题：", case["question"])
    print("期望工具：", expected_tools)
    print("实际工具：", called_tools)
    print("Agent回答：", answer)
    print("结果：", result)


print()
print(
    f"总成绩：{passed}/{len(eval_cases)}"
)

print(
    f"通过率："
    f"{passed / len(eval_cases) * 100:.0f}%"
)