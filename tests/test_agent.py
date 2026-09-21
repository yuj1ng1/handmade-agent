from types import SimpleNamespace
from agent import Agent
import json

class fakeclient:
    pass

def test_handle_tool_call_success():
    agent=Agent(
        client=fakeclient(),
        system_prompt="test"
    )
    def add(a,b):
        return a+b
    
    schema={
        "type":"function",
        "name":"add"
    }

    agent.register_tool(
        name="add",
        func=add,
        schema=schema,
        cacheable=True
        )
    
    item=SimpleNamespace(
        name="add",
        arguments='{"a":2,"b":3}',
        call_id="abc"
    )

    tool_cache={}

    tool_call_count,output_item=agent.handle_tool_call(
        item=item,
        tool_cache=tool_cache,
        tool_call_count=0,
        max_tool_calls=8
        )
    assert tool_call_count==1
    assert output_item["type"]=="function_call_output"
    assert output_item["call_id"]=="abc"
    assert output_item["output"]

def test_handle_tool_call_cache_hit():
    agent=Agent(
        client=fakeclient,
        system_prompt="test"
    )
    called={"count":0}

    def add(a,b):
        called["count"]+=1
        return a+b
    
    schema={
        "type":"function",
        "name":"add"
    }

    agent.register_tool(
        name="add",
        func=add,
        schema=schema,
        cacheable=True
        )
    
    item=SimpleNamespace(
        name="add",
        arguments='{"a":2,"b":3}',
        call_id="abc"
    )

    tool_cache={
        (
        "add",
        json.dumps(
            {"a":2,"b":3},
            ensure_ascii=False,
            sort_keys=True
        )
    ):5
    }

    tool_call_count,output_item=agent.handle_tool_call(
        item=item,
        tool_cache=tool_cache,
        tool_call_count=1,
        max_tool_calls=8
        )
    assert tool_call_count==1
    assert called["count"]==0
    assert output_item["output"]=="5"

def test_handle_tool_call_notcacheable():
    agent=Agent(
        client=fakeclient(),
        system_prompt="test"
    )
    called={"count":0}

    def add(a,b):
        called["count"]+=1
        return a+b
    
    schema={
        "type":"function",
        "name":"add"
    }

    agent.register_tool(
        name="add",
        func=add,
        schema=schema,
        cacheable=False
        )
    
    item=SimpleNamespace(
        name="add",
        arguments='{"a":2,"b":3}',
        call_id="abc"
    )

    tool_cache={
        (
        "add",
        json.dumps(
            {"a":2,"b":3},
            ensure_ascii=False,
            sort_keys=True
        )
    ):5555
    }

    tool_call_count,output_item=agent.handle_tool_call(
        item=item,
        tool_cache=tool_cache,
        tool_call_count=1,
        max_tool_calls=8
        )
    assert tool_call_count==2
    assert called["count"]==1
    assert output_item["output"]=="5"


def test_handle_tool_call_uptolimit():
    agent=Agent(
        client=fakeclient(),
        system_prompt="test"
    )
    def add(a,b):
        return a+b
    
    schema={
        "type":"function",
        "name":"add"
    }

    agent.register_tool(
        name="add",
        func=add,
        schema=schema,
        cacheable=True
        )
    
    item=SimpleNamespace(
        name="add",
        arguments='{"a":2,"b":3}',
        call_id="abc"
    )

    tool_cache={}

    tool_call_count,output_item=agent.handle_tool_call(
        item=item,
        tool_cache=tool_cache,
        tool_call_count=7,
        max_tool_calls=8
        )
    assert tool_call_count==8

def test_handle_tool_call_outlimit():
    agent=Agent(
        client=fakeclient(),
        system_prompt="test"
    )
    called={"count":0}
    def add(a,b):
        called["count"]+=1
        return a+b
    
    schema={
        "type":"function",
        "name":"add"
    }

    agent.register_tool(
        name="add",
        func=add,
        schema=schema,
        cacheable=True
        )
    
    item=SimpleNamespace(
        name="add",
        arguments='{"a":2,"b":3}',
        call_id="abc"
    )

    tool_cache={}

    tool_call_count,output_item=agent.handle_tool_call(
        item=item,
        tool_cache=tool_cache,
        tool_call_count=8,
        max_tool_calls=8
        )
    assert tool_call_count==8
    assert "次数已达上限" in output_item["output"]
    assert called["count"]==0

def test_ask_final_answer():
    agent=Agent(
        client=fakeclient(),
        system_prompt="test"
    )
    class FakeModelClient:
        def call_model(self,input_data,instructions,tools):
            return SimpleNamespace(
                output=[],
                output_text="return correct"
            )
    agent.model_client=FakeModelClient()

    result=agent.ask("this is test")

    assert result=="return correct"
    assert agent.history[-1]=={
        "role":"assistant",
        "content":"return correct"
    }

def test_react():
    agent=Agent(
        client=fakeclient(),
        system_prompt="test"
    )
    called={"count":0}

    def add(a,b):
        called["count"]+=1
        return a+b
    
    schema={
        "type":"function",
        "name":"add"
    }

    agent.register_tool(
        name="add",
        func=add,
        schema=schema,
        cacheable=True
    )

    class FakeModelclient:
        def __init__(self):
            self.call_count=0

        def call_model(self,input_data,instructions,tools):
            self.call_count+=1
            if self.call_count==1:
                function_call=SimpleNamespace(
                    type="function_call",
                    name="add",
                    arguments='{"a":2,"b":3}',
                    call_id="abc"
                )
                return SimpleNamespace(
                    output=[function_call],
                    output_text=""
                )

            return SimpleNamespace(
                output=[],
                output_text="5"
            )
    fake_model=FakeModelclient()
    agent.model_client=fake_model
    result=agent.ask("2+3=?")

    assert result=="5"
    assert fake_model.call_count==2
    assert called["count"]==1  

def test_react_inputs():
    agent=Agent(
        client=fakeclient(),
        system_prompt="test"
    )
    called={"count":0}

    def add(a,b):
        called["count"]+=1
        return a+b
    
    schema={
        "type":"function",
        "name":"add"
    }

    agent.register_tool(
        name="add",
        func=add,
        schema=schema,
        cacheable=True
    )

    class FakeModelclient:
        def __init__(self):
            self.call_count=0
            self.inputs=[]

        def call_model(self,input_data,instructions,tools):
            self.call_count+=1
            self.inputs.append(list(input_data))
            if self.call_count==1:
                function_call=SimpleNamespace(
                    type="function_call",
                    name="add",
                    arguments='{"a":2,"b":3}',
                    call_id="abc"
                )
                return SimpleNamespace(
                    output=[function_call],
                    output_text=""
                )

            return SimpleNamespace(
                output=[],
                output_text="5"
            )
    fake_model=FakeModelclient()
    agent.model_client=fake_model
    result=agent.ask("2+3=?")

    assert result=="5"
    assert fake_model.call_count==2
    assert called["count"]==1  

    second_input=fake_model.inputs[1]
    tool_output=[
        item
        for item in second_input
        if isinstance(item,dict) and item.get("type")=="function_call_output"
    ]
    assert tool_output[0]["call_id"]=="abc"
    assert tool_output[0]["output"]=="5"

def test_react_maxloop():
    agent=Agent(
        client=fakeclient(),
        system_prompt="test"
    )
    called={"count":0}

    def add(a,b):
        called["count"]+=1
        return a+b
    
    schema={
        "type":"function",
        "name":"add"
    }

    agent.register_tool(
        name="add",
        func=add,
        schema=schema,
        cacheable=True
    )

    class FakeModelclient:
        def __init__(self):
            self.call_count=0

        def call_model(self,input_data,instructions,tools):
            self.call_count+=1
            function_call=SimpleNamespace(
                    type="function_call",
                    name="add",
                    arguments='{"a": 2, "b": 3}',
                    call_id="abc"
            )
            return SimpleNamespace(
                output=[function_call],
                output_text=""
                )

            # return SimpleNamespace(
            #     output=[],
            #     output_text="5"
            # )
    fake_model=FakeModelclient()
    agent.model_client=fake_model
    result=agent.ask("2+3=?")

    assert fake_model.call_count == agent.max_loop_round
    assert called["count"] == 1
    assert "达到上限" in result

def test_react_tool_error():
    agent = Agent(
        client=fakeclient(),
        system_prompt="test"
    )

    called = {"count": 0}

    def divide(a, b):
        called["count"] += 1
        return a / b

    schema = {
        "type": "function",
        "name": "divide"
    }

    agent.register_tool(
        name="divide",
        func=divide,
        schema=schema,
        cacheable=True
    )

    class FakeModelClient:
        def __init__(self):
            self.call_count = 0
            self.inputs = []

        def call_model(
            self,
            input_data,
            instructions,
            tools
        ):
            self.call_count += 1
            self.inputs.append(list(input_data))

            if self.call_count == 1:
                function_call = SimpleNamespace(
                    type="function_call",
                    name="divide",
                    arguments='{"a":10,"b":0}',
                    call_id="abc"
                )

                return SimpleNamespace(
                    output=[function_call],
                    output_text=""
                )

            return SimpleNamespace(
                output=[],
                output_text="除数不能为0"
            )

    fake_model = FakeModelClient()
    agent.model_client = fake_model

    result = agent.ask("10除以0是多少？")

    assert result == "除数不能为0"
    assert fake_model.call_count == 2
    assert called["count"] == 1

def test_failed_tool_not_cached():
    agent = Agent(
        client=fakeclient(),
        system_prompt="test"
    )

    called = {"count": 0}

    def divide(a, b):
        called["count"] += 1
        return a / b

    schema = {
        "type": "function",
        "name": "divide"
    }

    agent.register_tool(
        name="divide",
        func=divide,
        schema=schema,
        cacheable=True
    )

    item = SimpleNamespace(
        name="divide",
        arguments='{"a":10,"b":0}',
        call_id="abc"
    )

    tool_cache = {}

    tool_call_count, output_item1 = agent.handle_tool_call(
        item=item,
        tool_cache=tool_cache,
        tool_call_count=0,
        max_tool_calls=8
    )

    tool_call_count, output_item2 = agent.handle_tool_call(
        item=item,
        tool_cache=tool_cache,
        tool_call_count=tool_call_count,
        max_tool_calls=8
    )

    assert called["count"] == 2
    assert tool_call_count == 2
    assert tool_cache == {}
    assert "执行失败" in output_item1["output"]
    assert "执行失败" in output_item2["output"]