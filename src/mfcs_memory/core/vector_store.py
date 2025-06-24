"""
Vector Store Module - Responsible for handling vector storage and retrieval
"""

import uuid
from typing import ClassVar, Dict, List, Optional
from datetime import datetime, timezone
from qdrant_client.models import PointStruct, VectorParams, Distance
import logging
import asyncio

from ..utils.config import Config
from .session_manager import SessionManager
from .base import ManagerBase

logger = logging.getLogger(__name__)

class VectorStore(ManagerBase):
    _initialized: ClassVar[bool] = False
    qdrant_collection: ClassVar[str] = 'memory_dialog_history'

    def __init__(self, config: Config, session_manager: SessionManager):
        super().__init__(config)
        self.session_manager = session_manager
        self._initialize()

    def _initialize(self) -> None:
        """Initialize vector collection"""
        if self._initialized:
            return

        collections = self.qdrant_client.get_collections()
        if self.qdrant_collection not in [c.name for c in collections.collections]:
            self.qdrant_client.recreate_collection(
                collection_name=self.qdrant_collection,
                vectors_config=VectorParams(
                    size=self.config.embedding_dim,
                    distance=Distance.COSINE
                )
            )
            logger.info(f"Created new collection: {self.qdrant_collection}")
        VectorStore._initialized = True

    async def reset(self) -> bool:
        """Clear all vector data
        
        Returns:
            bool: Whether the operation was successful
        """
        try:
            # Delete and recreate collection
            await asyncio.to_thread(
                self.qdrant_client.recreate_collection,
                collection_name=self.qdrant_collection,
                vectors_config=VectorParams(
                    size=self.config.embedding_dim,
                    distance=Distance.COSINE
                )
            )
            logger.info(f"Reset all vector data in collection: {self.qdrant_collection}")
            return True
        except Exception as e:
            logger.error(f"Error resetting vector data: {str(e)}")
            return False

    async def delete_user_dialogs(self, memory_id: str) -> bool:
        """Delete all dialog vectors related to a memory_id"""
        try:
            await asyncio.to_thread(
                self.qdrant_client.delete,
                collection_name=self.qdrant_collection,
                points_selector={"filter": {"must": [{"key": "memory_id", "match": {"value": memory_id}}]}}
            )
            logger.info(f"Deleted all data for memory_id {memory_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting memory_id data: {str(e)}")
            return False

    async def search_dialog_with_chunk(self, session_id: str, query: str, top_k: int = 2) -> List[Dict]:
        """Search for relevant historical dialogs, supporting chunked storage
        
        Args:
            session_id: Session ID
            query: Query text
            top_k: Number of relevant dialogs to return
            
        Returns:
            List[Dict]: List of relevant dialogs
        """
        # Generate embedding vector for query text
        query_embedding = self.embedding_model.encode(query)
        # Search in Qdrant
        results = await asyncio.to_thread(
            self.qdrant_client.search,
            collection_name=self.qdrant_collection,
            query_vector=query_embedding,
            limit=top_k
        )
        
        relevant_dialogs = []
        for hit in results:
            session_id = hit.payload["session_id"]
            chunk_id = hit.payload.get("chunk_id")
            message_index = hit.payload["message_index"]
            is_in_chunk = hit.payload.get("is_in_chunk", False)
            
            try:
                if is_in_chunk and chunk_id:
                    # Search in chunk table
                    chunk = await self.session_manager.get_dialog_chunk(chunk_id)
                    if chunk and "dialogs" in chunk and message_index < len(chunk["dialogs"]):
                        relevant_dialogs.append(chunk["dialogs"][message_index])
                else:
                    # Search in main table
                    session = await self.session_manager.get_session(session_id)
                    if session and "dialog_history" in session and message_index < len(session["dialog_history"]):
                        relevant_dialogs.append(session["dialog_history"][message_index])
            except Exception as e:
                logger.error(f"Error querying historical records: {str(e)}")
                continue
                
        return relevant_dialogs

    async def save_dialog_with_chunk(self, session_id: str, user: str, assistant: str, memory_id: Optional[str] = None) -> None:
        """Save dialog to vector store, supporting chunked storage
        
        Args:
            session_id: Session ID
            user: User input
            assistant: Assistant response
            memory_id: Memory ID
        """
        try:
            # Get session information
            session = await self.session_manager.get_session(session_id)
            if not session:
                raise ValueError(f"Session {session_id} not found")
            
            # Create new chunk when dialog history exceeds MAX_RECENT_HISTORY
            if len(session["dialog_history"]) > self.config.max_recent_history:
                logger.info(f"Dialog history exceeds {self.config.max_recent_history} rounds, creating new chunk...")
                # Create new chunk
                chunk_id = await self.session_manager.create_dialog_chunk(session_id)
                if not chunk_id:
                    logger.warning("Warning: Failed to create chunk")
                    return
                
                # Update session chunk information
                result = await self.session_manager.update_session_chunks(
                    session_id,
                    chunk_id,
                    session["dialog_history"][-self.config.max_recent_history:]
                )
                
                if not result:
                    logger.warning("Warning: Failed to update chunk information")
                    return
                    
                session = result
                logger.info(f"Current number of chunks: {len(session['history_chunks'])}")
            
            # Generate embedding vector for dialog text
            dialog_text = f"User: {user}\nAssistant: {assistant}"
            embedding = self.embedding_model.encode(dialog_text)
            
            # Calculate message index (position of current dialog in history)
            message_index = len(session["dialog_history"]) - 1
            
            point_id = uuid.uuid4().hex
            
            # Get current dialog location (chunk or main table)
            current_chunk_id = None
            if len(session["dialog_history"]) > self.config.max_recent_history:
                current_chunk_id = session["history_chunks"][-1] if session.get("history_chunks") else None
            
            await asyncio.to_thread(
                self.qdrant_client.upsert,
                collection_name=self.qdrant_collection,
                points=[
                    PointStruct(
                        id=point_id,
                        vector=embedding,
                        payload={
                            "session_id": str(session["_id"]),
                            "memory_id": memory_id,
                            "chunk_id": str(current_chunk_id) if current_chunk_id else None,
                            "message_index": message_index,
                            "short_text": dialog_text,
                            "is_in_chunk": current_chunk_id is not None,
                            "created_at": datetime.now(timezone.utc).isoformat()
                        }
                    )
                ]
            )
            logger.info(f"Saved dialog to vector store with point_id: {point_id}")
            
        except Exception as e:
            logger.error(f"Error saving dialog to chunk: {str(e)}")
            raise
