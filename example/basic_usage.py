"""
Basic Usage Example - Demonstrating how to use the MFCS Memory System
"""

import asyncio
import os
from dotenv import load_dotenv
from mfcs_memory.utils.config import Config
from mfcs_memory.core.memory_manager import MemoryManager

async def main():
    config = Config.from_env()

    # Initialize memory manager
    memory_manager = MemoryManager(config)

    # Simulate conversation
    user_id = "test_user_001"
    dialogs = [
        ("Hello, I'd like to learn about Python programming", "Python is a simple yet powerful programming language. It has efficient data structures and can effectively implement object-oriented programming."),
        ("What are the main features of Python?", "Python's main features include: 1. Easy to learn 2. Free and open source 3. Portability 4. Rich library ecosystem 5. Object-oriented 6. Extensibility"),
        ("How to install Python?", "Steps to install Python: 1. Visit python.org to download the installer 2. Run the installer 3. Check 'Add Python to PATH' 4. Complete installation"),
        ("What is Python's package manager?", "Python's main package manager is pip, used for installing and managing Python packages. Use 'pip install' to install packages and 'pip list' to view installed packages."),
        ("What is a virtual environment?", "A virtual environment is an isolated workspace for Python projects, helping avoid package version conflicts between different projects. Use venv or virtualenv to create virtual environments.")
    ]

    # Save conversations
    for user_input, assistant_response in dialogs:
        # Update conversation
        await memory_manager.update(
            user_id,
            user_input,
            assistant_response
        )
        print(f"Saving conversation: {user_input[:20]}...")

    # Get memory information
    query = "How to start Python programming?"
    memory_info = await memory_manager.get(
        user_id,
        query=query,
        top_k=2
    )

    print("\nMemory Information:")
    print(memory_info)

if __name__ == "__main__":
    asyncio.run(main())
