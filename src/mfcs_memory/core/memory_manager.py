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
        # Register analysis task types for extensibility
        self.analysis_task_handlers = {
            "user_memory": self._analyze_user_memory,
            "conversation_summary": self._update_conversation_summary,
        }
        # Restore unfinished analysis tasks on startup
        asyncio.create_task(self._restore_pending_tasks())

    async def _restore_pending_tasks(self) -> None:
        """Restore all unfinished analysis tasks, using a handler registry for extensibility."""
        try:
            pending_tasks = await self.session_manager.get_pending_analysis_tasks()
            for task in pending_tasks:
                if "session_data" in task:
                    handler = self.analysis_task_handlers.get(task.get("task_type"))
                    if handler:
                        await handler(task["_id"], task["session_data"])
                    else:
                        logger.warning(f"Unknown task_type: {task.get('task_type')}, session_id={task.get('session_id')}, memory_id={task.get('memory_id')}")
                else:
                    error_msg = "Task missing session data, cannot restore"
                    logger.warning(f"Task failed: session_id={task['session_id']}, error={error_msg}")
                    await self.session_manager.fail_analysis_task(task["session_id"], error_msg)
        except Exception as e:
            logger.error(f"Error restoring pending tasks: {str(e)}")
            raise

    async def _run_analysis_tasks(self, session: Dict, content: str, assistant_response: str, memory_id: str) -> None:
        """Run analysis tasks asynchronously, using registered task types and enhanced logging."""
        dialog_count = len(session["dialog_history"])
        session_id = session["_id"]
        tasks = []
        logger.info(f"Creating vector store save task... memory_id={memory_id}, session_id={session_id}")
        tasks.append(asyncio.create_task(self.vector_store.save_dialog_with_chunk(session_id, content, assistant_response, memory_id)))
        if dialog_count >= 3 and dialog_count % 3 == 0:
            logger.info(f"Creating user memory analysis task... memory_id={memory_id}, session_id={session_id}")
            task_id = await self.session_manager.create_analysis_task(session, memory_id, "user_memory", dialog_count)
            if task_id:
                tasks.append(asyncio.create_task(self._analyze_user_memory(task_id, session)))
        if dialog_count >= 5 and dialog_count % 5 == 0:
            logger.info(f"Creating conversation summary task at {dialog_count} dialogs... memory_id={memory_id}, session_id={session_id}")
            task_id = await self.session_manager.create_analysis_task(session, memory_id, "conversation_summary", dialog_count)
            if task_id:
                tasks.append(asyncio.create_task(self._update_conversation_summary(task_id, session)))
        if tasks:
            task = asyncio.create_task(self._execute_analysis_tasks(session_id, tasks))
            self._analysis_tasks.add(task)
            task.add_done_callback(self._analysis_tasks.discard)

    async def _analyze_user_memory(self, task_id: str, session: Dict) -> None:
        """Analyze user memory with enhanced exception handling."""
        try:
            memory_id = session.get("memory_id")
            user_memory = await self.conversation_analyzer.analyze_user_profile(session["dialog_history"])
            if user_memory:
                session["user_memory_summary"] = user_memory
                await self.session_manager.save_session(session)
                await self.session_manager.complete_analysis_task(task_id)
                logger.info(f"User memory analysis completed, memory_id={memory_id}, session_id={session.get('_id')}, task_id={task_id}")
        except Exception as e:
            logger.error(f"Error in user memory analysis: {str(e)}, memory_id={session.get('memory_id')}, session_id={session.get('_id')}, task_id={task_id}")
            await self.session_manager.fail_analysis_task(task_id, str(e))

    async def _update_conversation_summary(self, task_id: str, session: Dict) -> None:
        """Update conversation summary with enhanced exception handling."""
        try:
            memory_id = session.get("memory_id")
            summary = await self.conversation_analyzer.update_conversation_summary(session)
            if summary:
                session["conversation_summary"] = summary
                await self.session_manager.save_session(session)
                await self.session_manager.complete_analysis_task(task_id)
                logger.info(f"Conversation summary update completed, memory_id={memory_id}, session_id={session.get('_id')}, task_id={task_id}")
        except Exception as e:
            logger.error(f"Error in conversation summary update: {str(e)}, memory_id={session.get('memory_id')}, session_id={session.get('_id')}, task_id={task_id}")
            await self.session_manager.fail_analysis_task(task_id, str(e))

    async def _execute_analysis_tasks(self, session_id: str, tasks: list) -> None:
        """Execute analysis tasks

        Args:
            session_id: Session ID
            tasks: List of tasks to execute
        """
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"Error executing analysis tasks for session {session_id}: {str(e)}")

    async def delete(self, memory_id: str) -> bool:
        """Delete all data for specified memory_id

        Args:
            memory_id: Memory ID

        Returns:
            bool: Whether deletion was successful
        """
        try:
            # Delete session data
            await self.session_manager.delete_user_session(memory_id)
            
            # Delete vector store data
            await self.vector_store.delete_user_dialogs(memory_id)
            
            logger.info(f"Successfully deleted all data for memory_id {memory_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting memory_id data: {str(e)}")
            return False

    async def reset(self) -> bool:
        """Reset all user records

        Returns:
            bool: Whether reset was successful
        """
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

    async def update(self, memory_id: str, content: str, assistant_response: str) -> bool:
        """Update conversation memory

        Args:
            memory_id: Memory ID
            content: User input content
            assistant_response: Assistant response

        Returns:
            bool: Whether update was successful
        """ 
        try:
            # Get or create current session for memory_id
            session = await self.session_manager.get_or_create_session(memory_id)
            session_id = session["_id"]
            
            # Update dialog history
            result = await self.session_manager.update_dialog_history(session_id, content, assistant_response)
            if not result:
                logger.warning("Failed to update dialog history")
                return False
            
            # Execute analysis tasks in background
            asyncio.create_task(self._run_analysis_tasks(result, content, assistant_response, memory_id))
            
            return True
        except Exception as e:
            logger.error(f"Error updating conversation memory: {str(e)}")
            return False

    async def get(self, memory_id: str, content: Optional[str] = None, top_k: int = 2) -> str:
        """Get memory information

        Args:
            memory_id: Memory ID
            content: Query content (e.g. user input)
            top_k: Number of relevant historical conversations to return

        Returns:
            str: Formatted memory information
        """
        # Get all sessions for the memory_id
        session = await self.session_manager.get_or_create_session(memory_id)
        session_id = session["_id"]

        prompt_parts = []

        # Add conversation summary
        if session.get("conversation_summary"):
            prompt_parts.append(f"【Conversation Summary】\n{session['conversation_summary']}")

        # Add user memory
        if session.get("user_memory_summary"):
            prompt_parts.append(f"【User Memory】\n{session['user_memory_summary']}")

        # Add relevant historical conversations
        if content and top_k > 0:
            relevant_history = await self.vector_store.search_dialog_with_chunk(session_id, content, top_k)
            if relevant_history:
                history_text = "\n".join([f"User: {d['user']}\nAssistant: {d['assistant']}" for d in relevant_history])
                prompt_parts.append(f"【Relevant History】\n{history_text}")

        return "\n".join(prompt_parts)

    async def cleanup(self) -> None:
        """Graceful shutdown: wait for all analysis tasks to complete and handle exceptions uniformly"""
        try:
            if self._analysis_tasks:
                pending_tasks = [task for task in self._analysis_tasks if not task.done()]
                if pending_tasks:
                    logger.info(f"Waiting for {len(pending_tasks)} analysis tasks to complete...")
                    results = await asyncio.gather(*pending_tasks, return_exceptions=True)
                    # Unified exception handling
                    for res in results:
                        if isinstance(res, Exception):
                            logger.error(f"Analysis task exception: {res}")
            logger.info("All analysis tasks completed, resources cleaned up")
        except Exception as e:
            logger.error(f"Error during graceful shutdown: {str(e)}")
            raise

    def running_task_count(self) -> int:
        """Count the number of unfinished analysis tasks"""
        return len([t for t in self._analysis_tasks if not t.done()])
