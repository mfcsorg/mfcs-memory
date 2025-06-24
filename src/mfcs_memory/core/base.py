"""
Base Manager Module - Responsible for managing shared connections and initialization
"""

import logging
import os
from typing import ClassVar
from pymongo import MongoClient
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

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
    mongo_client: ClassVar[MongoClient] = None
    qdrant_client: ClassVar[QdrantClient] = None
    embedding_model: ClassVar[SentenceTransformer] = None

    def __init__(self, config: Config):
        """Initialize base manager

        Args:
            config: Configuration object
        """
        self.config = config
        self._initialize()

    def _initialize(self) -> None:
        """Initialize all shared connections synchronously"""
        if ManagerBase._initialized:
            return

        try:
            # Initialize MongoDB connection
            uri = f'mongodb://{self.config.mongo_user}:{self.config.mongo_passwd}@{self.config.mongo_host}/admin'
            if self.config.mongo_replset:
                uri += f'?replicaSet={self.config.mongo_replset}'
            ManagerBase.mongo_client = MongoClient(uri)
            logger.info("MongoDB connection initialized successfully")

            # Initialize Qdrant connection
            ManagerBase.qdrant_client = QdrantClient(url=self.config.qdrant_url)
            logger.info("Qdrant connection initialized successfully")

            # Initialize embedding model
            ManagerBase.embedding_model = SentenceTransformer(self.config.embedding_model_path)
            logger.info("Embedding model initialized successfully")

            ManagerBase._initialized = True
            logger.info("All shared connections initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing shared connections: {str(e)}")
            raise
