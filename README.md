# MFCS Memory

[English](README.md) | [中文](README_zh.md)

MFCS Memory is an intelligent conversation memory management system that helps AI assistants remember conversation history with users and dynamically adjust response strategies based on conversation content.

## Key Features

- Intelligent Conversation Memory: Automatically analyzes and summarizes user characteristics and preferences
- Vector Storage: Uses Qdrant for efficient similar conversation retrieval
- Session Management: Supports multi-user, multi-session management
- Automatic Chunking: Automatically creates chunks when conversation history exceeds threshold
- Async Support: All operations support asynchronous execution
- Extensibility: Modular design, easy to extend and customize

## Core Features

### MemoryManager Core Methods

1. **get(user_id: str, query: Optional[str] = None, top_k: int = 2) -> str**
   - Get current session information for specified user
   - Includes conversation summary and user memory summary
   - Supports query-based relevant historical conversation retrieval
   - Returns formatted memory information

2. **update(user_id: str, user_input: str, assistant_response: str) -> bool**
   - Automatically gets or creates current session for user
   - Updates conversation history
   - Automatically updates user memory summary every 3 rounds
   - Automatically updates session summary every 5 rounds
   - Automatically handles conversation chunking

3. **delete(user_id: str) -> bool**
   - Deletes all data for specified user
   - Includes session data and vector storage data
   - Returns whether operation was successful

4. **reset() -> bool**
   - Resets all user records
   - Clears all session data and vector storage
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

Note: The default embedding model is `BAAI/bge-large-zh-v1.5`. You can change it in the configuration.

## Quick Start

1. First, create a `.env` file and configure necessary environment variables:

```env
# MongoDB Configuration
MONGO_USER=your_username
MONGO_PASSWD=your_password
MONGO_HOST=localhost:27017
MONGO_REPLSET=rs0  # Optional, if using replica set

# Qdrant Configuration
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION=dialog_vectors

# Model Configuration
EMBEDDING_MODEL_PATH=./model/BAAI/bge-large-zh-v1.5
EMBEDDING_DIM=768
LLM_MODEL=qwen-plus-latest  # Default value

# OpenAI Configuration
OPENAI_API_KEY=your_api_key

# Other Configuration
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
        "user123",
        "Hello, I want to learn about Python programming",
        "Python is a simple yet powerful programming language..."
    )
    
    # Get memory information
    memory_info = await memory_manager.get(
        "user123",
        query="How to start Python programming?",
        top_k=2
    )
    
    # Delete user data
    await memory_manager.delete("user123")
    
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
│   │   ├── memory_manager.py    # Memory Manager
│   │   ├── session_manager.py   # Session Manager
│   │   ├── vector_store.py      # Vector Store
│   │   └── conversation_analyzer.py  # Conversation Analyzer
│   ├── utils/
│   │   ├── config.py           # Configuration Management
│   │   └── logger.py           # Logging Utilities
│   └── __init__.py
├── example/                     # Example Code
├── tests/                      # Test Files
├── setup.py                    # Installation Configuration
└── README.md                   # Project Documentation
```

## Configuration Guide

### Required Configuration
- `MONGO_USER`: MongoDB username
- `MONGO_PASSWD`: MongoDB password
- `MONGO_HOST`: MongoDB host address
- `QDRANT_HOST`: Qdrant host address
- `QDRANT_COLLECTION`: Qdrant collection name
- `EMBEDDING_MODEL_PATH`: Model path for generating text vectors
- `OPENAI_API_KEY`: OpenAI API key
- `OPENAI_API_BASE`: OpenAI API Base

### Optional Configuration
- `MONGO_REPLSET`: MongoDB replica set name (if using replica set)
- `QDRANT_PORT`: Qdrant port number (default: 6333)
- `EMBEDDING_DIM`: Vector dimension (default: 768)
- `LLM_MODEL`: LLM model name (default: qwen-plus-latest)
- `MAX_RECENT_HISTORY`: Number of recent conversations kept in main table (default: 20)
- `CHUNK_SIZE`: Number of conversations stored in each chunk (default: 100)
- `MAX_CONCURRENT_ANALYSIS`: Maximum number of concurrent analysis tasks (default: 3)

## Contributing

Issues and Pull Requests are welcome!

## License

MIT License 