"""
Base Manager Module - Responsible for managing shared connections and initialization
"""

import logging
from typing import ClassVar, Optional
from openai import AsyncOpenAI
from pymongo import AsyncMongoClient
from qdrant_client.async_qdrant_client import AsyncQdrantClient
from sentence_transformers import SentenceTransformer
import asyncio

from ..utils.config import Config

logger = logging.getLogger(__name__)

class ManagerBase:
    """Base Manager Class
    
    Responsible for managing all shared connections and initialization, including:
    - MongoDB connection
    - Qdrant connection
    - Embedding model
    """
    
    _initialized: ClassVar[bool] = False
    _init_lock: ClassVar[asyncio.Lock] = asyncio.Lock()
    _init_task: ClassVar[Optional[asyncio.Task]] = None
    mongo_client: ClassVar[AsyncMongoClient] = None
    qdrant_client: ClassVar[AsyncQdrantClient] = None
    embedding_model: ClassVar[SentenceTransformer] = None
    openai_client: ClassVar[AsyncOpenAI] = None
    
    def __init__(self, config: Config):
        """Initialize base manager
        
        Args:
            config: Configuration object
        """
        self.config = config
        if not self._initialized and not self._init_task:
            # Create initialization task
            self._init_task = asyncio.create_task(self._initialize())
            
    async def _initialize(self) -> None:
        """Initialize all shared connections"""
        if ManagerBase._initialized:
            return
            
        async with self._init_lock:
            if ManagerBase._initialized:  # Double check
                return
                
            try:
                # Initialize MongoDB connection
                uri = f'mongodb://{self.config.mongo_user}:{self.config.mongo_passwd}@{self.config.mongo_host}/admin'
                if self.config.mongo_replset:
                    uri += f'?replicaSet={self.config.mongo_replset}'
                ManagerBase.mongo_client = AsyncMongoClient(uri)
                logger.info("MongoDB connection initialized successfully")
                
                # Initialize Qdrant connection
                ManagerBase.qdrant_client = AsyncQdrantClient(
                    self.config.qdrant_host,
                    port=self.config.qdrant_port
                )
                logger.info("Qdrant connection initialized successfully")
                
                # Initialize embedding model
                ManagerBase.embedding_model = SentenceTransformer(self.config.embedding_model_path)
                logger.info("Embedding model initialized successfully")
                
                # Initialize OpenAI connection
                ManagerBase.openai_client = AsyncOpenAI(api_key=self.config.openai_api_key, base_url=self.config.openai_api_base)
                logger.info("OpenAI connection initialized successfully")
                
                ManagerBase._initialized = True
                logger.info("All shared connections initialized successfully")
                
            except Exception as e:
                logger.error(f"Error initializing shared connections: {str(e)}")
                raise
                
    async def ensure_initialized(self) -> None:
        """Ensure initialization is complete"""
        if not self._initialized and self._init_task:
            try:
                await self._init_task
            except Exception as e:
                logger.error(f"Error waiting for initialization to complete: {str(e)}")
                raise 