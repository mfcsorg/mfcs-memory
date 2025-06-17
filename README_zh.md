# MFCS Memory

[English](README.md) | [中文](README_zh.md)

MFCS Memory 是一个智能对话记忆管理系统，它能够帮助AI助手记住与用户的对话历史，并根据对话内容动态调整回复策略。

## 主要特性

- 智能对话记忆：自动分析和总结用户特征和偏好
- 向量化存储：使用Qdrant进行高效的相似对话检索
- 会话管理：支持多用户、多会话的管理
- 自动分块：当对话历史超过阈值时自动创建分块
- 异步支持：所有操作都支持异步执行
- 可扩展性：模块化设计，易于扩展和定制

## 核心功能

### MemoryManager 核心方法

1. **get(user_id: str, query: Optional[str] = None, top_k: int = 2) -> str**
   - 获取指定用户的当前会话信息
   - 包括对话摘要、用户记忆摘要
   - 支持基于查询的相关历史对话检索
   - 返回格式化的记忆信息

2. **update(user_id: str, user_input: str, assistant_response: str) -> bool**
   - 自动获取或创建用户的当前会话
   - 更新对话历史
   - 每3轮对话自动更新用户记忆摘要
   - 每5轮对话自动更新会话摘要
   - 自动处理对话分块

3. **delete(user_id: str) -> bool**
   - 删除指定用户的所有数据
   - 包括会话数据和向量存储数据
   - 返回操作是否成功

4. **reset() -> bool**
   - 重置所有用户的记录
   - 清空所有会话数据和向量存储
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

注意：默认的嵌入模型是 `BAAI/bge-large-zh-v1.5`。您可以在配置中更改此设置。

## 快速开始

1. 首先，创建一个 `.env` 文件并配置必要的环境变量：

```env
# MongoDB配置
MONGO_USER=your_username
MONGO_PASSWD=your_password
MONGO_HOST=localhost:27017

# Qdrant配置
QDRANT_HOST=localhost
QDRANT_PORT=6333

# 模型配置
EMBEDDING_MODEL_PATH=./model/BAAI/bge-large-zh-v1.5
EMBEDDING_DIM=768
LLM_MODEL=qwen-plus-latest  # 默认值

# OpenAI配置
OPENAI_API_KEY=your_api_key
OPENAI_API_BASE=your_api_base  # 可选

# 其他配置
MONGO_REPLSET=''  # 可选，如果使用副本集
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
        "user123",
        "你好，我想了解一下Python编程",
        "Python是一种简单易学且功能强大的编程语言..."
    )
    
    # 获取记忆信息
    memory_info = await memory_manager.get(
        "user123",
        query="如何开始Python编程？",
        top_k=2
    )
    
    # 删除用户数据
    await memory_manager.delete("user123")
    
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
│   │   ├── memory_manager.py    # 内存管理器
│   │   ├── session_manager.py   # 会话管理器
│   │   ├── vector_store.py      # 向量存储
│   │   └── conversation_analyzer.py  # 对话分析器
│   ├── utils/
│   │   ├── config.py           # 配置管理
│   │   └── logger.py           # 日志工具
│   └── __init__.py
├── example/                     # 示例代码
├── tests/                      # 测试文件
├── setup.py                    # 安装配置
└── README.md                   # 项目说明
```

## 配置说明

### 必需配置
- `MONGO_USER`: MongoDB 用户名
- `MONGO_PASSWD`: MongoDB 密码
- `MONGO_HOST`: MongoDB 主机地址
- `QDRANT_HOST`: Qdrant 主机地址
- `EMBEDDING_MODEL_PATH`: 用于生成文本向量的模型路径
- `EMBEDDING_DIM`: 向量维度
- `OPENAI_API_KEY`: OpenAI API 密钥
- `OPENAI_API_BASE`: OpenAI API 地址

### 可选配置
- `MONGO_REPLSET`: MongoDB 副本集名称（如果使用副本集）
- `QDRANT_PORT`: Qdrant 端口号（默认：6333）
- `LLM_MODEL`: LLM 模型名称（默认：qwen-plus-latest）
- `MAX_RECENT_HISTORY`: 保存在主表中的最近对话数量（默认：20）
- `CHUNK_SIZE`: 每个分块中存储的对话数量（默认：100）
- `MAX_CONCURRENT_ANALYSIS`: 最大并发分析任务数（默认：3）

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License 