import os
from opencc import OpenCC
from datetime import datetime
from tool_registry import tool
from http_utils import (get_with_retry,post_with_retry)
from knowledge_base import KnowledgeBase
from retriever import Retriever
from langchain_rag import LangChainRag

@tool
def search_wiki(keyword):#docstring必须是函数中的第一条语句
    """
    搜索 Wikipedia 中稳定的百科知识。

    适用于人物、历史、地理、科学概念等长期稳定的信息。
    不适用于最新新闻、近期事件、当前版本、
    最新发布等实时信息，这类问题应使用 web_search。

    Args:
        keyword: 需要查询的百科关键词
    """
    search_url="https://zh.wikipedia.org/w/rest.php/v1/search/page"

    search_params={
        "q":keyword,
        "limit":1
    }
    search_headers={
            "User-Agent": "MyPythonAgent/1.0 (learning project)"
    }
    response=get_with_retry(url=search_url,params=search_params,headers=search_headers)
    result=response.json()

    pages=result["pages"]
    if not pages:
        return f"没有查询到：{keyword}"

    data=pages[0]

    cc = OpenCC("t2s")
    title=cc.convert(data["title"])
    excerpt=cc.convert(data["excerpt"])

    return (
        f"标题：{title}"
        f"摘要：{excerpt}"
    )


@tool
def get_weather(city:str):
    """
    查询指定城市的当前天气信息。

    Args:
        city: 需要查询天气的城市名称
    """
    geo_url="https://geocoding-api.open-meteo.com/v1/search"

    geo_params={
        "name":city,
        "count":1,
        "language":"zh"
    }
    geo_response=get_with_retry(url=geo_url,params=geo_params)
    geo_data=geo_response.json()

    if not geo_data.get("results"):
        return f"未查询到城市：{city}"
    
    location=geo_data["results"][0]
    latitude=location["latitude"]
    longitude=location["longitude"]
    city_name=location["name"]

    weather_url="https://api.open-meteo.com/v1/forecast"

    weather_params={
        "latitude":latitude,
        "longitude":longitude,
        "current":"temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m",
        "timezone":"auto"
    }

    wea_response=get_with_retry(url=weather_url,params=weather_params)
    weather_data=wea_response.json()

    current=weather_data["current"]
    temperature = current["temperature_2m"]
    humidity = current["relative_humidity_2m"]
    wind_speed = current["wind_speed_10m"]
    weather_code = current["weather_code"]

    return (
        f"{city_name}当前温度：{temperature}度"
        f"湿度：{humidity}%,"
        f"风速：{wind_speed}km/h,"
        f"天气代码：{weather_code}"
    )


@tool
def calculate(a:float,b:float,operation:str):
    """
    执行两个数字之间的加减乘除运算。

    Args:
        a: 第一个数字
        b: 第二个数字
        operation: 运算类型，可选 add、sub、mul、div
    """
    print("calculate")
    if operation=="add":
        return a+b
    elif operation=="sub":
        return a-b
    elif operation=="div":
        if b==0:
            raise ValueError("除数不得为0")
        return a/b
    elif operation=="mul":
        return a*b
    else: raise ValueError("无效操作")

@tool(cacheable=False)
def get_time():
    """
    获取当前系统日期和时间。
    """
    print("get_time")
    now=datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S") #格式化时间

@tool
def web_search(query:str):
    """
    搜索互联网中的实时和最新信息。

    适用于新闻、最新发布、近期事件、当前版本、
    当前价格、赛事安排以及其他可能发生变化的信息。
    遇到实时信息时应优先使用本工具，而不是 Wikipedia。

    Args:
        query: 需要联网搜索的问题或关键词
    """
    api_key=os.getenv("ALIYUN_IQS_API_KEY")
    iqs_url="https://cloud-iqs.aliyuncs.com/search/unified"

    headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    json_data={
        "query":query,
        "engineType":"Generic",
        "contents": {
            "mainText":True,
            "markdownText":False,
            "summary": False,
            "rerankScore": True
        },
        "advancedParams":{
            "numResults": 5
        }
    }

    response=post_with_retry(
        url=iqs_url,
        headers=headers,
        json_data=json_data
    )

    data=response.json()
    page_items=data.get("pageItems",[])
    if not page_items:
        return f"没有搜索到相关内容：{query}"
    
    text=""
    for i,item in enumerate(page_items, start=1):
        text+=(
            f"搜索来源{i}：\n"
            f"标题：{item.get('title','')}\n"
            f"链接：{item.get('link','')}\n"
            f"发布时间：{item.get('publishedTime','')}\n"
            f"摘要：{item.get('snippet','')}\n"
            f"正文：{item.get('mainText','')}\n"
        )
    return text


# knowledge_base=KnowledgeBase()
# retriever=Retriever(
#     knowledge_base,
#     top_k=3
# )
# @tool
# def search_knowledge(question:str)->list[str]:
#     """
#     从本地《程序设计实训完整报告》知识库中检索与问题最相关的资料。

#     当用户询问实训报告中的题目分析、算法思路、复杂度、
#     测试结果、核心代码或其他报告内容时使用此工具。
#     不用于查询实时信息或报告之外的通用知识。

#     Args:
#         question: 要在本地知识库中检索的问题或关键词。

#     Returns:
#         与问题最相关的若干文本片段及其相似度信息。
#     """
    
#     return retriever.retrieve(question)

langchain_rag=LangChainRag()
@tool()
def ask_knowledge(question:str)->str:
    """
    从本地《程序设计实训完整报告》知识库中检索资料并回答问题。

    当用户询问实训报告中的题目分析、算法思路、复杂度、
    测试结果、核心代码或其他报告内容时使用此工具。

    Args:
        question: 用户关于本地实训报告提出的问题。

    Returns:
        基于本地知识库生成的回答。
    """   
    return langchain_rag.ask(question)

