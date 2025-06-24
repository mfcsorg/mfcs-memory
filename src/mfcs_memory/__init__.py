"""
MFCS Memory - A smart conversation memory management system
"""

# Version information
__version__ = "0.1.8"

# Export all required classes
from .utils.config import Config
from .core.memory_manager import MemoryManager
from .core.session_manager import SessionManager
from .core.vector_store import VectorStore
from .core.conversation_analyzer import ConversationAnalyzer

__all__ = [
    'Config',
    'MemoryManager',
    'SessionManager',
    'VectorStore',
    'ConversationAnalyzer',
]