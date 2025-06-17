"""
Memory Manager Module - Core component for managing conversation memory
"""

import logging
import asyncio
from typing import Dict, Optional, Set

from ..utils.config import Config
from .conversation_analyzer import ConversationAnalyzer
from .session_manager import SessionManager
from .vector_store import VectorStore
from .base import ManagerBase

logger = logging.getLogger(__name__)

class MemoryManager(ManagerBase):
    def __init__(self, config: Config):
        super().__init__(config)
        self.conversation_analyzer = ConversationAnalyzer(config)
        self.session_manager = SessionManager(config)
        self.vector_store = VectorStore(config, self.session_manager)
        self._analysis_tasks: Set[asyncio.Task] = set()
        
        # Restore unfinished analysis tasks on startup
        asyncio.create_task(self._restore_pending_tasks())

    async def _restore_pending_tasks(self) -> None:
        """Restore unfinished analysis tasks"""
        await self.ensure_initialized()
        try:
            # Get all pending tasks
            pending_tasks = await self.session_manager.get_pending_analysis_tasks()
            
            for task in pending_tasks:
                if "session_data" in task:
                    # Recreate analysis tasks using saved session data
                    await self._run_analysis_tasks(task["session_data"], task["user_input"], task["assistant_response"], task["user_id"])
                else:
                    # Mark tasks without session data as failed
                    error_msg = "Task missing session data, cannot restore"
                    logger.warning(f"Task failed: session_id={task['session_id']}, error={error_msg}")
                    await self.session_manager.fail_analysis_task(task["session_id"], error_msg)
                    
        except Exception as e:
            logger.error(f"Error restoring pending tasks: {str(e)}")
            raise

    async def _run_analysis_tasks(self, session: Dict, user_input: str, assistant_response: str, user_id: str) -> None:
        """Run analysis tasks asynchronously
        
        Args:
            session: Session data
            user_input: User input
            assistant_response: Assistant response
            user_id: User ID
        """
        await self.ensure_initialized()
        dialog_count = len(session["dialog_history"])
        session_id = session["_id"]
        
        # Create analysis tasks
        tasks = []
        
        # Save dialog to vector store task
        logger.info("Creating vector store save task...")
        tasks.append(asyncio.create_task(self.vector_store.save_dialog_with_chunk(session_id, user_input, assistant_response, user_id)))
        
        # User memory analysis task
        if dialog_count >= 3 and dialog_count % 3 == 0:
            logger.info("Creating user memory analysis task...")
            # Record task status and save session data
            await self.session_manager.create_analysis_task(session, user_input, assistant_response, user_id)
            tasks.append(asyncio.create_task(self._analyze_user_memory(session)))
            
        # Conversation summary analysis task
        if dialog_count >= 5 and dialog_count % 5 == 0:
            logger.info(f"Creating conversation summary task at {dialog_count} dialogs...")
            # Record task status and save session data
            await self.session_manager.create_analysis_task(session, user_input, assistant_response, user_id)
            tasks.append(asyncio.create_task(self._update_conversation_summary(session)))
            
        if tasks:
            # Create new task set
            task = asyncio.create_task(self._execute_analysis_tasks(session_id, tasks))
            self._analysis_tasks.add(task)
            task.add_done_callback(self._analysis_tasks.discard)

    async def _analyze_user_memory(self, session: Dict) -> None:
        """Analyze user memory
        
        Args:
            session: Session data
        """
        await self.ensure_initialized()
        session_id = session["_id"]
        try:
            user_memory = await self.conversation_analyzer.analyze_user_profile(session["dialog_history"])
            if user_memory:
                session["user_memory_summary"] = user_memory
                await self.session_manager.save_session(session)
                # Mark task as completed
                await self.session_manager.complete_analysis_task(session_id)
                logger.info("User memory analysis completed")
        except Exception as e:
            logger.error(f"Error in user memory analysis: {str(e)}")
            # Mark task as failed
            await self.session_manager.fail_analysis_task(session_id, str(e))

    async def _update_conversation_summary(self, session: Dict) -> None:
        """Update conversation summary
        
        Args:
            session: Session data
        """
        await self.ensure_initialized()
        session_id = session["_id"]
        try:
            summary = await self.conversation_analyzer.update_conversation_summary(session)
            if summary:
                session["conversation_summary"] = summary
                await self.session_manager.save_session(session)
                # Mark task as completed
                await self.session_manager.complete_analysis_task(session_id)
                logger.info("Conversation summary update completed")
        except Exception as e:
            logger.error(f"Error in conversation summary update: {str(e)}")
            # Mark task as failed
            await self.session_manager.fail_analysis_task(session_id, str(e))

    async def _execute_analysis_tasks(self, session_id: str, tasks: list) -> None:
        """Execute analysis tasks
        
        Args:
            session_id: Session ID
            tasks: List of tasks to execute
        """
        await self.ensure_initialized()
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"Error executing analysis tasks for session {session_id}: {str(e)}")

    async def delete(self, user_id: str) -> bool:
        """Delete all data for specified user
        
        Args:
            user_id: User ID
            
        Returns:
            bool: Whether deletion was successful
        """
        await self.ensure_initialized()
        try:
            # Delete session data
            await self.session_manager.delete_user_session(user_id)
            
            # Delete vector store data
            await self.vector_store.delete_user_dialogs(user_id)
            
            logger.info(f"Successfully deleted all data for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting user data: {str(e)}")
            return False

    async def reset(self) -> bool:
        """Reset all user records
        
        Returns:
            bool: Whether reset was successful
        """
        await self.ensure_initialized()
        try:
            # Clear session data
            await self.session_manager.reset()
            
            # Clear vector store data
            await self.vector_store.reset()
            
            logger.info("Successfully reset all user records")
            return True
        except Exception as e:
            logger.error(f"Error resetting all records: {str(e)}")
            return False

    async def update(self, user_id: str, user_input: str, assistant_response: str) -> bool:
        """Update conversation memory
        
        Args:
            user_id: User ID
            user_input: User input
            assistant_response: Assistant response
            
        Returns:
            Dict: Updated session information
        """ 
        await self.ensure_initialized()
        # Get or create current session for user
        session = await self.session_manager.get_or_create_session(user_id)
        session_id = session["_id"]

        # Update dialog history
        result = await self.session_manager.update_dialog_history(session_id, user_input, assistant_response)
        if not result:
            logger.warning("Failed to update dialog history")
            return False

        # Execute all tasks asynchronously
        await self._run_analysis_tasks(result, user_input, assistant_response, user_id)
        
        return True

    async def get(self, user_id: str, query: Optional[str] = None, top_k: int = 2) -> str:
        """Get memory information
        
        Args:
            user_id: User ID
            query: Query text for retrieving relevant historical conversations
            top_k: Number of relevant historical conversations to return
            
        Returns:
            str: Formatted memory information
        """
        await self.ensure_initialized()
        # Get all sessions for the user
        session = await self.session_manager.get_or_create_session(user_id)
        session_id = session["_id"]

        prompt_parts = []

        # Add conversation summary
        if session.get("conversation_summary"):
            prompt_parts.append(f"【Conversation Summary】\n{session['conversation_summary']}")

        # Add user memory
        if session.get("user_memory_summary"):
            prompt_parts.append(f"【User Memory】\n{session['user_memory_summary']}")

        # Add relevant historical conversations
        if query:
            relevant_history = await self.vector_store.search_dialog_with_chunk(session_id, query, top_k)
            if relevant_history:
                history_text = "\n".join([f"User: {d['user']}\nAssistant: {d['assistant']}" for d in relevant_history])
                prompt_parts.append(f"【Relevant History】\n{history_text}")

        return "\n".join(prompt_parts)
