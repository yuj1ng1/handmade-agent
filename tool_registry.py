import inspect

tool_registry={}

def tool(func=None,*,cacheable=True):
    def decorator(f):
        schema=generate_schema(f)

        tool_registry[f.__name__]={
                "func":f,
                "schema":schema,
                "cacheable":cacheable
            }
        return f
    if func is not None:
        return decorator(func)
    return decorator

#func.__name__返回的是函数自己的名字
#tool_registry["calculate"] = {
#     "func": calculate,
#     "schema": calculate_schema
# }

def generate_schema(func):
    type_map = {
        str: "string",
        int: "integer",
        float: "number",
        bool: "boolean"
    }

    sig=inspect.signature(func)
    doc=inspect.getdoc(func)or""

    lines=doc.splitlines()

    description=""
    param_descriptions={}#函数中元素的描述
    in_arg=False

    for line in lines:
        stripped_line = line.strip()

        if not description and stripped_line and stripped_line != "Args:":
            description=stripped_line #函数的功能描述

        if stripped_line == "Args:":
            in_arg=True
            continue
        if in_arg and ":" in stripped_line:
            name,param_description=stripped_line.split(":",1) #将元素名以描述分别解包
            param_descriptions[name.strip()]=param_description.strip()#a={"description":param_description.strip()}

    properties={}
    required=[]


    #开始映射函数的参数(此处为name)
    for name,param in sig.parameters.items():
        json_type=type_map.get(param.annotation,"string")

        properties[name]={
            "type":json_type,
            "description":param_descriptions.get(name,"")
        }
        if param.default is inspect._empty:
            required.append(name)
    
    return {
        "type": "function",
        "name": func.__name__,
        "description": description,
        "parameters": {
            "type": "object",
            "properties": properties,
            "required": required
        }
    }