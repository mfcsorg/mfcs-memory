# MFCS Memory

[English](README.md) | [中文](README_zh.md)

MFCS Memory 是一个智能对话记忆管理系统，能够帮助AI助手记住与用户的对话历史，并根据对话内容动态调整回复策略。

## 主要特性

- **智能对话记忆**：自动分析和总结用户特征与偏好
- **向量化存储**：使用Qdrant高效检索相似对话
- **会话管理**：支持多用户、多会话管理
- **自动分块**：对话历史超阈值时自动分块存储
- **异步支持**：所有操作均支持异步执行
- **可扩展性**：模块化设计，易于扩展和定制
- **自动LLM分析**：用户记忆和会话摘要按设定轮数自动异步分析与更新

## 核心模块

- `core/base.py`：基础管理器，负责所有共享连接（MongoDB、Qdrant、嵌入模型）
- `core/conversation_analyzer.py`：基于LLM（OpenAI API）分析对话内容和用户画像
- `core/memory_manager.py`：记忆管理主入口，调度各模块与异步任务
- `core/session_manager.py`：会话创建、更新、分块与分析任务管理
- `core/vector_store.py`：向量存储、检索与分块对话管理
- `utils/config.py`：加载并校验所有环境变量配置

## 核心功能

### MemoryManager 核心方法

1. **get(memory_id: str, content: Optional[str] = None, top_k: int = 2) -> str**
   - 获取指定记忆ID当前会话信息
   - 包含会话摘要和用户记忆摘要
   - 支持基于内容的相关历史对话检索（向量搜索）
   - 返回格式化记忆信息

2. **update(memory_id: str, content: str, assistant_response: str) -> bool**
   - 自动获取或创建当前记忆ID的会话
   - 更新对话历史
   - 每3轮自动异步分析并更新用户记忆（LLM分析）
   - 每5轮自动异步分析并更新会话摘要（LLM分析）
   - 自动处理对话分块与向量存储
   - 所有分析任务异步执行，支持重启恢复

3. **delete(memory_id: str) -> bool**
   - 删除指定记忆ID所有数据（会话+向量存储）
   - 返回操作是否成功

4. **reset() -> bool**
   - 重置所有记忆记录（清空所有会话和向量数据）
   - 返回操作是否成功

## 安装

1. 安装主包：
```bash
pip install mfcs-memory
```

2. 安装 SentenceTransformer 用于文本嵌入：
```bash
pip install sentence-transformers
```

> **注意：** 默认嵌入模型为 `BAAI/bge-large-zh-v1.5`，可在配置中自定义。

## 快速开始

1. 创建 `.env` 文件并配置必要环境变量：

```env
# MongoDB配置
MONGO_USER=your_username
MONGO_PASSWD=your_password
MONGO_HOST=localhost:27017

# Qdrant配置
QDRANT_URL=http://127.0.0.1:6333

# 模型配置
EMBEDDING_MODEL_PATH=./model/BAAI/bge-large-zh-v1.5
EMBEDDING_DIM=768
LLM_MODEL=qwen-plus-latest  # 默认值

# OpenAI配置
OPENAI_API_KEY=your_api_key
OPENAI_API_BASE=your_api_base  # 可选

# 其他配置
MONGO_REPLSET=''  # 可选，副本集
MAX_RECENT_HISTORY=20  # 默认值
CHUNK_SIZE=100  # 默认值
MAX_CONCURRENT_ANALYSIS=3  # 默认值
```

2. 使用示例：

```python
import asyncio
from mfcs_memory.utils.config import Config
from mfcs_memory.core.memory_manager import MemoryManager

async def main():
    # 加载配置
    config = Config.from_env()
    
    # 初始化内存管理器
    memory_manager = MemoryManager(config)
    
    # 更新对话
    await memory_manager.update(
        "memory_123",
        "你好，我想了解一下Python编程",
        "Python是一种简单易学且功能强大的编程语言..."
    )
    
    # 获取记忆信息
    memory_info = await memory_manager.get(
        "memory_123",
        content="如何开始Python编程？",
        top_k=2
    )
    
    # 删除记忆数据
    await memory_manager.delete("memory_123")
    
    # 重置所有数据
    await memory_manager.reset()

if __name__ == "__main__":
    asyncio.run(main())
```

## 项目结构

```
src/
├── mfcs_memory/
│   ├── core/
│   │   ├── base.py                # 基础管理器（连接）
│   │   ├── memory_manager.py      # 记忆管理主逻辑
│   │   ├── session_manager.py     # 会话/分块/任务管理
│   │   ├── vector_store.py        # 向量存储（Qdrant）
│   │   ├── conversation_analyzer.py # 对话分析（LLM）
│   │   └── __init__.py
│   ├── utils/
│   │   ├── config.py              # 配置管理
│   │   └── __init__.py
│   └── __init__.py
├── example/                       # 示例代码
├── model/                         # 模型目录
├── setup.py                       # 安装配置
├── .env.example                   # 环境变量示例
└── README.md                      # 项目说明
```

## 配置说明

### 必需配置
- `MONGO_USER`：MongoDB用户名
- `MONGO_PASSWD`：MongoDB密码
- `MONGO_HOST`：MongoDB主机地址
- `QDRANT_URL`：Qdrant连接地址
- `EMBEDDING_MODEL_PATH`：用于生成文本向量的模型路径
- `EMBEDDING_DIM`：向量维度
- `OPENAI_API_KEY`：OpenAI API密钥
- `OPENAI_API_BASE`：OpenAI API地址（可选）
- `LLM_MODEL`：LLM模型名称

### 可选配置
- `MONGO_REPLSET`：MongoDB副本集名称（如使用副本集）
- `QDRANT_PORT`：Qdrant端口号（默认：6333）
- `MAX_RECENT_HISTORY`：主表中保留的最近对话数量（默认：20）
- `CHUNK_SIZE`：每个分块存储的对话数量（默认：100）
- `MAX_CONCURRENT_ANALYSIS`：最大并发分析任务数（默认：3）

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License