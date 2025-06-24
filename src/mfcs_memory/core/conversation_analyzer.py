"""
Conversation Analyzer Module - Responsible for analyzing conversation content and user profiles
"""

import logging
from typing import Dict, List
from openai import AsyncOpenAI

from ..utils.config import Config
from .base import ManagerBase

logger = logging.getLogger(__name__)

class ConversationAnalyzer(ManagerBase):
    def __init__(self, config: Config):
        super().__init__(config)

        # Initialize OpenAI client
        self.openai_client = AsyncOpenAI(
            api_key=self.config.openai_api_key,
            base_url=self.config.openai_api_base
        )
        logger.info("OpenAI connection initialized successfully")

    async def analyze_user_profile(self, dialog_history: List[Dict], n: int = 5) -> str:
        """Analyze user profile

        Args:
            dialog_history: List of conversation history records
            n: Number of recent conversations to process

        Returns:
            str: User profile analysis result
        """
        recent_history = dialog_history[-n:]
        history_text = "\n".join([f"User: {d['user']}\nAssistant: {d['assistant']}" for d in recent_history])

        analysis_prompt = f'''
Please carefully read the following conversation history and automatically summarize and extract all important settings, rules, identity, interests, preferences, etc. that the user has for you. Please use imperative language like "You must..." or "You should..." to clearly express the behavioral norms and role settings you need to follow in subsequent conversations.

Requirements:
- Don't just make factual descriptions, use imperative language to summarize.
- Summarize all user-expressed identities, titles, rules, interests, styles, etc.
- Only output imperative settings, don't add other explanations.
- Don't mention the assistant's AI identity, robot identity, user's inquiries about assistant identity, or any AI-related content in the summary.
- You must not fabricate, complete, or make up any information, and can only respond based on the user's real input and historical conversation content.

Conversation History:
{history_text}
'''
        try:
            response = await self.openai_client.chat.completions.create(
                model=self.config.llm_model,
                messages=[
                    {"role": "system", "content": "You are a professional conversation analysis assistant. Only output imperative settings, don't add other explanations."},
                    {"role": "user", "content": analysis_prompt}
                ]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error analyzing user profile: {str(e)}", exc_info=True)
            return ""

    async def update_conversation_summary(self, session: Dict, n: int = 5) -> str:
        """Update conversation summary

        Args:
            session: Session data
            n: Number of recent conversations to process

        Returns:
            str: Updated conversation summary
        """
        logger.info(f"\nStarting conversation summary update, session_id: {session.get('_id')}")
        if not session:
            logger.error("Cannot update conversation summary: session does not exist")
            return ""

        summary = session.get("conversation_summary", "")
        dialog_history = session.get("dialog_history", [])
        logger.info(f"Current conversation history length: {len(dialog_history)}")

        # Get recent N rounds
        new_dialogs = dialog_history[-n:]
        new_dialogs_text = "\n".join([f"User: {d['user']}\nAssistant: {d['assistant']}" for d in new_dialogs])
        logger.info(f"Preparing conversation content for summary generation:\n{new_dialogs_text}")

        # Construct summary prompt
        summary_prompt = f"""
You are a professional conversation analysis assistant. Please directly generate a concise conversation summary without adding any prefixes or explanatory text.

Requirements:
1. Output the summary content directly, don't add prefixes like "New conversation summary:"
2. Combine existing summary and new conversations to generate a new summary
3. Preserve all important historical information
4. Keep it within 200 words
5. Use objective and concise language

Existing Summary:
{summary}

New Conversations:
{new_dialogs_text}
"""
        try:
            # Call LLM to generate summary
            response = await self.openai_client.chat.completions.create(
                model=self.config.llm_model,
                messages=[
                    {"role": "system", "content": "You are a professional conversation analysis assistant. Output summary content directly without adding any prefixes or explanatory text."},
                    {"role": "user", "content": summary_prompt}
                ]
            )
            new_summary = response.choices[0].message.content.strip()
            logger.info(f"Generated summary content:\n{new_summary}")
            return new_summary
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}", exc_info=True)
            return ""
