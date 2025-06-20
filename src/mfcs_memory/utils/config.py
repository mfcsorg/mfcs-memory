"""
Configuration Module - Manages system configuration and environment variables
"""

import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

@dataclass
class Config:
    """Configuration Class
    
    Used to manage all configuration items for the application, including:
    - MongoDB configuration: database connection information
    - Qdrant configuration: vector database connection information
    - Model configuration: embedding model and LLM model configuration
    - OpenAI configuration: API key
    - Other configuration: history length, chunk size, etc.
    """
    # Required configurations
    mongo_user: str
    mongo_passwd: str
    mongo_host: str
    qdrant_url: str
    embedding_model_path: str
    embedding_dim: int
    openai_api_key: str
    llm_model: str
    
    # Optional configurations
    openai_api_base: Optional[str] = None
    mongo_replset: Optional[str] = None
    qdrant_port: int = 6333
    max_recent_history: int = 20  # Number of recent conversations to keep in main table
    chunk_size: int = 100  # Number of conversations per chunk
    max_concurrent_analysis: int = 3  # Maximum number of concurrent analysis tasks

    def __post_init__(self):
        """Validate configuration"""
        # Validate required configurations
        required_configs = {
            "MongoDB User": self.mongo_user,
            "MongoDB Password": self.mongo_passwd,
            "MongoDB Host": self.mongo_host,
            "Qdrant URL": self.qdrant_url,
            "Embedding Model Path": self.embedding_model_path,
            "Embedding Dimension": self.embedding_dim,
            "OpenAI API Key": self.openai_api_key,
            "LLM Model": self.llm_model
        }
        
        missing_configs = [name for name, value in required_configs.items() if not value]
        if missing_configs:
            raise ValueError(f"Missing required configurations: {', '.join(missing_configs)}")
        
        # Validate numeric configurations
        if self.mongo_user is None:
            raise ValueError("MongoDB user is required")
        if self.mongo_passwd is None:
            raise ValueError("MongoDB password is required")
        if self.mongo_host is None:
            raise ValueError("MongoDB host is required")
        if self.qdrant_url is None:
            raise ValueError("Qdrant URL is required")
        if self.embedding_model_path is None:
            raise ValueError("Embedding model path is required")
        if self.embedding_dim <= 0:
            raise ValueError("Embedding dimension must be positive")
        if self.openai_api_key is None:
            raise ValueError("OpenAI API key is required")
        if self.llm_model is None:
            raise ValueError("LLM model is required")

    @classmethod
    def from_env(cls, env_file: Optional[str] = None) -> 'Config':
        """Load configuration from environment variables
        
        Args:
            env_file: Path to environment variable file, if None uses default .env file
            
        Returns:
            Config: Configuration object
            
        Raises:
            ValueError: When required configuration is missing or configuration value is invalid
        """
        if env_file:
            load_dotenv(env_file)
        else:
            load_dotenv()

        return cls(
            # MongoDB configuration
            mongo_user=os.getenv("MONGO_USER"),
            mongo_passwd=os.getenv("MONGO_PASSWD"),
            mongo_host=os.getenv("MONGO_HOST"),

            # Qdrant configuration
            qdrant_url=os.getenv("QDRANT_URL"),

            # Model configuration
            embedding_model_path=os.getenv("EMBEDDING_MODEL_PATH"),
            embedding_dim=int(os.getenv("EMBEDDING_DIM")),

            # OpenAI configuration
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_api_base=os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1"),
            llm_model=os.getenv("LLM_MODEL"),

            # Other configuration
            mongo_replset=os.getenv("MONGO_REPLSET"),
            max_recent_history=int(os.getenv("MAX_RECENT_HISTORY", "20")),
            chunk_size=int(os.getenv("CHUNK_SIZE", "100")),
            max_concurrent_analysis=int(os.getenv("MAX_CONCURRENT_ANALYSIS", "3"))
        )
