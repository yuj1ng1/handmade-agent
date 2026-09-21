# calculate_schema = {
#     "type": "function",
#     "name": "calculate",
#     "description": "执行两个数字之间的加减乘除运算",
#     "parameters": {
#         "type": "object",
#         "properties": {
#             "a": {
#                 "type": "number",
#                 "description": "第一个数字"
#             },
#             "b": {
#                 "type": "number",
#                 "description": "第二个数字"
#             },
#             "operation": {
#                 "type": "string",
#                 "enum": ["add", "sub", "div", "mul"]
#             }
#         },
#         "required": ["a", "b", "operation"]
#     }
# }

# weather_schema = {
#     "type": "function",
#     "name": "get_weather",
#     "description": "查询指定城市的实时天气",
#     "parameters": {
#         "type": "object",
#         "properties": {
#             "city": {
#                 "type": "string",
#                 "description": "城市名称"
#             }
#         },
#         "required": ["city"]
#     }
# }

# time_schema = {
#     "type": "function",
#     "name": "get_time",
#     "description": "查询当前时间",
#     "parameters": {
#         "type": "object",
#         "properties": {},
#         "required": []
#     }
# }

# wiki_schema = {
#     "type": "function",
#     "name": "search_wiki",
#     "description": "根据关键词查询维基百科",
#     "parameters": {
#         "type": "object",
#         "properties": {
#             "keyword": {
#                 "type": "string",
#                 "description": "需要查询的关键词"
#             }
#         },
#         "required": ["keyword"]
#     }
# }