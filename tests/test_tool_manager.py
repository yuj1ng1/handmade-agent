from tool_manager import ToolManager
from types import SimpleNamespace

def test_register_tool():
    manager = ToolManager()

    def hello():
        return "hello"

    schema = {
        "type": "function",
        "name": "hello"
    }

    manager.register_tool(
        name="hello",
        func=hello,
        schema=schema,
        cacheable=True
    )

    tool_info = manager.get_tool_info("hello")

    assert tool_info["func"] is hello
    assert tool_info["schema"] == schema
    assert tool_info["cacheable"] is True

def test_run_tool_success(): #正常测试
    manager = ToolManager()

    def add(a, b):
        return a + b

    schema = {
        "type": "function",
        "name": "add"
    }

    manager.register_tool(
        name="add",
        func=add,
        schema=schema,
        cacheable=True
    )

    item = SimpleNamespace(
        name="add",
        arguments='{"a": 2, "b": 3}'
    )

    success, result = manager.run_tool(item)

    assert success is True
    assert result == 5

def test_run_tool_not_found(): #测试不存在的工具
    manager = ToolManager()

    item = SimpleNamespace(
        name="not_exist",
        arguments="{}"
    )

    success, result = manager.run_tool(item)

    assert success is False
    assert "查询not_exist工具失败" in result

def test_run_tool_invalid_json():#测试无效json
    manager = ToolManager()

    def add(a, b):
        return a + b

    schema = {
        "type": "function",
        "name": "add"
    }

    manager.register_tool(
        name="add",
        func=add,
        schema=schema,
        cacheable=True
    )

    item = SimpleNamespace(
        name="add",
        arguments='{"a": 2, "b": }'#此处为错误格式的json
    )

    success, result = manager.run_tool(item)

    assert success is False
    assert "参数格式错误" in result

def test_run_tool_execution_error():#测试工具执行失败
    manager = ToolManager()

    def divide(a, b):
        return a / b

    schema = {
        "type": "function",
        "name": "divide"
    }

    manager.register_tool(
        name="divide",
        func=divide,
        schema=schema,
        cacheable=True
    )

    item = SimpleNamespace(
        name="divide",
        arguments='{"a": 10, "b": 0}'
    )

    success, result = manager.run_tool(item)

    assert success is False
    assert "执行失败" in result