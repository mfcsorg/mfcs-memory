# MFCS Memory

[English](README.md) | [中文](README_zh.md)

MFCS Memory is an intelligent conversation memory management system that helps AI assistants remember conversation history with users and dynamically adjust response strategies based on conversation content.

## Key Features

- **Intelligent Conversation Memory**: Automatically analyzes and summarizes user characteristics and preferences
- **Vector Storage**: Uses Qdrant for efficient similar conversation retrieval
- **Session Management**: Supports multi-user, multi-session management
- **Automatic Chunking**: Automatically creates chunks when conversation history exceeds threshold
- **Async Support**: All operations support asynchronous execution
- **Extensibility**: Modular design, easy to extend and customize
- **Automatic LLM-based Analysis**: User memory and conversation summary are updated automatically at configurable intervals

## Core Modules

- `core/base.py`: Base manager, handles all shared connections (MongoDB, Qdrant, embedding model)
- `core/conversation_analyzer.py`: Analyzes conversation content and user profile using LLM (OpenAI API)
- `core/memory_manager.py`: Main entry for memory management, orchestrates all modules and async tasks
- `core/session_manager.py`: Handles session creation, update, chunking, and analysis task management
- `core/vector_store.py`: Handles vector storage, retrieval, and chunked dialog management
- `utils/config.py`: Loads and validates all configuration from environment variables

## Core Features

### MemoryManager Core Methods

1. **get(memory_id: str, content: Optional[str] = None, top_k: int = 2) -> str**
   - Get current session information for specified memory_id
   - Includes conversation summary and user memory summary
   - Supports content-based relevant historical conversation retrieval (vector search)
   - Returns formatted memory information

2. **update(memory_id: str, content: str, assistant_response: str) -> bool**
   - Automatically gets or creates current session for memory_id
   - Updates conversation history
   - Automatically updates user memory summary every 3 rounds (LLM analysis)
   - Automatically updates session summary every 5 rounds (LLM analysis)
   - Automatically handles conversation chunking and vector storage
   - All analysis tasks run asynchronously and are recoverable on restart

3. **delete(memory_id: str) -> bool**
   - Deletes all data for specified memory_id (session + vector store)
   - Returns whether operation was successful

4. **reset() -> bool**
   - Resets all memory records (clears all session and vector data)
   - Returns whether operation was successful

## Installation

1. Install the package:
```bash
pip install mfcs-memory
```

2. Install SentenceTransformer for text embedding:
```bash
pip install sentence-transformers
```

> **Note:** The default embedding model is `BAAI/bge-large-zh-v1.5`. You can change it in the configuration.

## Quick Start

1. Create a `.env` file and configure necessary environment variables:

```env
# MongoDB Configuration
MONGO_USER=your_username
MONGO_PASSWD=your_password
MONGO_HOST=localhost:27017

# Qdrant Configuration
QDRANT_URL=http://127.0.0.1:6333

# Model Configuration
EMBEDDING_MODEL_PATH=./model/BAAI/bge-large-zh-v1.5
EMBEDDING_DIM=768
LLM_MODEL=qwen-plus-latest  # Default value

# OpenAI Configuration
OPENAI_API_KEY=your_api_key
OPENAI_API_BASE=your_api_base  # Optional

# Other Configuration
MONGO_REPLSET=''  # Optional, if using replica set
MAX_RECENT_HISTORY=20  # Default value
CHUNK_SIZE=100  # Default value
MAX_CONCURRENT_ANALYSIS=3  # Default value
```

2. Usage Example:

```python
import asyncio
from mfcs_memory.utils.config import Config
from mfcs_memory.core.memory_manager import MemoryManager

async def main():
    # Load configuration
    config = Config.from_env()
    
    # Initialize memory manager
    memory_manager = MemoryManager(config)
    
    # Update conversation
    await memory_manager.update(
        "memory_123",
        "Hello, I want to learn about Python programming",
        "Python is a simple yet powerful programming language..."
    )
    
    # Get memory information
    memory_info = await memory_manager.get(
        "memory_123",
        content="How to start Python programming?",
        top_k=2
    )
    
    # Delete memory data
    await memory_manager.delete("memory_123")
    
    # Reset all data
    await memory_manager.reset()

if __name__ == "__main__":
    asyncio.run(main())
```

## Project Structure

```
src/
├── mfcs_memory/
│   ├── core/
│   │   ├── base.py                # Base manager (connections)
│   │   ├── memory_manager.py      # Memory manager (main logic)
│   │   ├── session_manager.py     # Session manager (session, chunk, task)
│   │   ├── vector_store.py        # Vector store (Qdrant)
│   │   ├── conversation_analyzer.py # Conversation analyzer (LLM)
│   │   └── __init__.py
│   ├── utils/
│   │   ├── config.py              # Configuration management
│   │   └── __init__.py
│   └── __init__.py
├── example/                       # Example code
├── model/                         # Model directory
├── setup.py                       # Installation config
├── .env.example                   # Environment file example
└── README.md                      # Project documentation
```

## Configuration Guide

### Required Configuration
- `MONGO_USER`: MongoDB username
- `MONGO_PASSWD`: MongoDB password
- `MONGO_HOST`: MongoDB host address
- `QDRANT_URL`: Qdrant url address
- `EMBEDDING_MODEL_PATH`: Model path for generating text vectors
- `EMBEDDING_DIM`: Vector dimension
- `OPENAI_API_KEY`: OpenAI API key
- `OPENAI_API_BASE`: OpenAI API base URL (Optional)
- `LLM_MODEL`: LLM model name

### Optional Configuration
- `MONGO_REPLSET`: MongoDB replica set name (if using replica set)
- `QDRANT_PORT`: Qdrant port number (default: 6333)
- `MAX_RECENT_HISTORY`: Number of recent conversations kept in main table (default: 20)
- `CHUNK_SIZE`: Number of conversations stored in each chunk (default: 100)
- `MAX_CONCURRENT_ANALYSIS`: Maximum number of concurrent analysis tasks (default: 3)

## Contributing

Issues and Pull Requests are welcome!

## License

MIT License