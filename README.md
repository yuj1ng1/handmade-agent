# 手搓 Agent

这是一个用于学习 Agent 工作机制的 Python 项目，包含模型调用、工具注册与执行、短期/长期记忆、重试处理、知识库检索和基础测试。

## 主要内容

- `agent.py`：Agent 主循环与工具调用处理
- `tool_registry.py` / `tool_manager.py`：工具注册、执行、缓存与限制
- `model_client.py` / `http_utils.py`：模型与 HTTP 请求封装
- `memory_manager.py` / `memory_store.py`：上下文和本地记忆管理
- `knowledge_base.py` / `retriever.py`：本地文档向量检索
- `tools.py`：百科、天气、计算、时间、搜索与知识库工具
- `tests/`：核心逻辑单元测试

## 本地运行

1. 建议使用 Python 3.11 或 3.12 创建虚拟环境。
2. 安装依赖：

   ```powershell
   python -m pip install -r requirements.txt
   ```

3. 复制 `.env.example` 为 `.env`，并填写要使用的服务密钥。
4. 启动命令行 Agent：

   ```powershell
   python main.py
   ```

输入 `exit` 或 `quit` 可退出。

## 测试

```powershell
python -m pytest tests -q
```

知识库相关实验还需要 `faiss-cpu`、`sentence-transformers` 和本地文档。`rag_text/`、向量索引、运行日志、对话记忆与 `.env` 默认不提交到仓库。

## 安全说明

不要把真实 API Key 写入代码或提交到 Git。请仅在本地 `.env` 文件中保存密钥。
