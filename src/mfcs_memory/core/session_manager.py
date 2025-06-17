"""
Session Manager Module - Responsible for handling session creation and management
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Optional, List
from bson import ObjectId

from ..utils.config import Config
from .base import ManagerBase

logger = logging.getLogger(__name__)

class SessionManager(ManagerBase):
    """Session Manager"""
    
    def __init__(self, config: Config):
        """Initialize session manager
        
        Args:
            config: Configuration object
        """
        super().__init__(config)
        self.mongo_db = 'mfcs_memory'

    async def create_session(self, user_id: str) -> Dict:
        """Create new session"""
        await self.ensure_initialized()
        session = await self.mongo_client[self.mongo_db]['memory_sessions'].find_one({"user_id": user_id})
        if session:
            return session

        session = {
            "user_id": user_id,
            "user_memory_summary": "",
            "dialog_history": [],
            "conversation_summary": "",
            "history_chunks": [],
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        result = await self.mongo_client[self.mongo_db]['memory_sessions'].insert_one(session)
        session["_id"] = result.inserted_id
        logger.info(f"Created new session for user {user_id}")
        return session

    async def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session information"""
        await self.ensure_initialized()
        return await self.mongo_client[self.mongo_db]['memory_sessions'].find_one({"_id": ObjectId(session_id)})

    async def save_session(self, session: Dict) -> None:
        """Save session information"""
        await self.ensure_initialized()
        session["updated_at"] = datetime.now(timezone.utc)
        await self.mongo_client[self.mongo_db]['memory_sessions'].update_one(
            {"_id": session["_id"]},
            {"$set": session},
            upsert=True
        )
        logger.info(f"Saved session {session['_id']}")

    async def delete_user_session(self, user_id: str) -> bool:
        """Delete session"""
        await self.ensure_initialized()
        result = await self.mongo_client[self.mongo_db]['memory_sessions'].delete_one({"user_id": user_id})
        success = result.deleted_count > 0
        if success:
            logger.info(f"Deleted user {user_id} session")
        else:
            logger.warning(f"Failed to delete user {user_id} session")
        return success

    async def reset(self) -> bool:
        """Clear all session data
        
        Returns:
            bool: Whether operation was successful
        """
        await self.ensure_initialized()
        try:
            # Delete all session data
            await self.mongo_client[self.mongo_db]['memory_sessions'].delete_many({})
            # Delete all dialog chunk data
            await self.mongo_client[self.mongo_db]['memory_dialog_chunks'].delete_many({})
            logger.info("Reset all session data")
            return True
        except Exception as e:
            logger.error(f"Error resetting session data: {str(e)}")
            return False

    async def update_dialog_history(self, session_id: str, user_input: str, assistant_response: str) -> Optional[Dict]:
        """Update session dialog history
        
        Args:
            session_id: Session ID
            user_input: User input
            assistant_response: Assistant response
            
        Returns:
            Optional[Dict]: Updated session information, returns None if update fails
        """
        await self.ensure_initialized()
        try:
            result = await self.mongo_client[self.mongo_db]['memory_sessions'].find_one_and_update(
                {"_id": ObjectId(session_id)},
                {
                    "$push": {"dialog_history": {"user": user_input, "assistant": assistant_response}},
                    "$set": {"updated_at": datetime.now(timezone.utc)}
                },
                return_document=True
            )
            
            if result:
                logger.info(f"Updated dialog history for session {session_id}")
            else:
                logger.warning(f"Failed to update dialog history for session {session_id}")
                
            return result
        except Exception as e:
            logger.error(f"Error updating dialog history: {str(e)}")
            return None

    async def create_dialog_chunk(self, session_id: str) -> Optional[str]:
        """Create new dialog chunk
        
        Args:
            session_id: Session ID
            
        Returns:
            Optional[str]: Chunk ID, returns None if creation fails
        """
        await self.ensure_initialized()
        try:
            # Get current session information for calculating chunk index
            session = await self.get_session(session_id)
            if not session:
                raise ValueError(f"Session {session_id} not found")

            chunk_id = str(ObjectId())
            chunk_doc = {
                "_id": chunk_id,
                "session_id": session_id,
                "start_index": len(session.get("history_chunks", [])) * self.config.chunk_size,
                "dialogs": session["dialog_history"][:-self.config.max_recent_history],
                "created_at": datetime.now(timezone.utc)
            }
            await self.mongo_client[self.mongo_db]["memory_dialog_chunks"].insert_one(chunk_doc)
            logger.info(f"Created new chunk: {chunk_id}")
            return chunk_id
        except Exception as e:
            logger.error(f"Error creating dialog chunk: {str(e)}")
            return None

    async def update_session_chunks(self, session_id: str, chunk_id: str, recent_dialogs: List[Dict]) -> Optional[Dict]:
        """Update session chunk information
        
        Args:
            session_id: Session ID
            chunk_id: Chunk ID
            recent_dialogs: Recent dialogs to keep in main table
            
        Returns:
            Optional[Dict]: Updated session information, returns None if update fails
        """
        await self.ensure_initialized()
        try:
            result = await self.mongo_client[self.mongo_db]['memory_sessions'].find_one_and_update(
                {"_id": ObjectId(session_id)},
                {
                    "$push": {"history_chunks": chunk_id},
                    "$set": {
                        "dialog_history": recent_dialogs,
                        "updated_at": datetime.now(timezone.utc)
                    }
                },
                return_document=True
            )
            
            if result:
                logger.info(f"Updated session chunks for session {session_id}")
            else:
                logger.warning(f"Failed to update session chunks for session {session_id}")
                
            return result
        except Exception as e:
            logger.error(f"Error updating session chunks: {str(e)}")
            return None

    async def get_dialog_chunk(self, chunk_id: str) -> Optional[Dict]:
        """Get dialog chunk
        
        Args:
            chunk_id: Chunk ID
            
        Returns:
            Optional[Dict]: Chunk information, returns None if not found
        """
        await self.ensure_initialized()
        return await self.mongo_client[self.mongo_db]["memory_dialog_chunks"].find_one({"_id": chunk_id})

    async def get_or_create_session(self, user_id: str) -> Dict:
        """Get or create current session for user
        
        Args:
            user_id: User ID
            
        Returns:
            Dict: Session information
        """
        await self.ensure_initialized()
        # Find user's latest session
        session = await self.mongo_client[self.mongo_db]['memory_sessions'].find_one(
            {"user_id": user_id},
            sort=[("updated_at", -1)]
        )
        
        if session:
            return session
            
        # If no session found, create new session
        return await self.create_session(user_id)

    async def create_analysis_task(self, session: Dict, user_input: str, assistant_response: str, user_id: str) -> None:
        """Create analysis task record
        
        Args:
            session: Session data
            user_input: User input
            assistant_response: Assistant response
            user_id: User ID
        """
        await self.ensure_initialized()
        task = {
            "session_id": str(session["_id"]),
            "user_id": user_id,
            "user_input": user_input,
            "assistant_response": assistant_response,
            "status": "pending",
            "session_data": session,  # Save session data
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        await self.mongo_client[self.mongo_db]['analysis_tasks'].insert_one(task)
        logger.info(f"Created analysis task for session {session['_id']}")

    async def complete_analysis_task(self, session_id: str) -> None:
        """Mark analysis task as completed
        
        Args:
            session_id: Session ID
        """
        await self.ensure_initialized()
        await self.mongo_client[self.mongo_db]['analysis_tasks'].update_one(
            {
                "session_id": session_id,
                "status": "pending"
            },
            {
                "$set": {
                    "status": "completed",
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )
        logger.info(f"Completed analysis task for session {session_id}")

    async def fail_analysis_task(self, session_id: str, error: str) -> None:
        """Mark analysis task as failed
        
        Args:
            session_id: Session ID
            error: Error message
        """
        await self.ensure_initialized()
        await self.mongo_client[self.mongo_db]['analysis_tasks'].update_one(
            {
                "session_id": session_id,
                "status": "pending"
            },
            {
                "$set": {
                    "status": "failed",
                    "error": error,
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )
        logger.error(f"Failed analysis task for session {session_id}, error: {error}")

    async def get_pending_analysis_tasks(self) -> List[Dict]:
        """Get all pending analysis tasks
        
        Returns:
            List[Dict]: List of pending tasks
        """
        await self.ensure_initialized()
        cursor = self.mongo_client[self.mongo_db]['analysis_tasks'].find(
            {"status": "pending"},
            sort=[("created_at", 1)]
        )
        return await cursor.to_list(length=None)
