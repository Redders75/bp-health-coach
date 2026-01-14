"""
Natural language query answering feature.
"""
from typing import Dict, Any, Optional

from src.orchestration.conversation_manager import ConversationManager


class QueryEngine:
    """Engine for answering natural language health queries."""

    def __init__(self, session_id: Optional[str] = None):
        """
        Initialize the query engine.

        Args:
            session_id: Optional session ID for conversation continuity
        """
        self.conversation_manager = ConversationManager(session_id)

    def ask(self, query: str) -> str:
        """
        Answer a natural language query about health data.

        Args:
            query: User's question in natural language

        Returns:
            Natural language response
        """
        result = self.conversation_manager.process_query(query)
        return result['response']

    def ask_with_metadata(self, query: str) -> Dict[str, Any]:
        """
        Answer a query and return full metadata.

        Args:
            query: User's question

        Returns:
            Dict with response and metadata
        """
        return self.conversation_manager.process_query(query)

    def get_session_id(self) -> str:
        """Get the current session ID."""
        return self.conversation_manager.session_id

    def new_session(self) -> str:
        """Start a new conversation session."""
        self.conversation_manager.clear_session()
        return self.conversation_manager.session_id
