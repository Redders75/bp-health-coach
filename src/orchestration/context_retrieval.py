"""
Context retrieval for LLM queries.
"""
from datetime import date, timedelta
from typing import Dict, Any, Optional, Tuple

from src.data.database import (
    get_health_data_for_date,
    get_health_data_range,
    get_recent_conversations,
    get_user_baselines
)
from src.data.vector_store import get_vector_store
from src.orchestration.intent_classifier import IntentType, ClassifiedIntent
from config.settings import user_profile


class ContextRetriever:
    """Retrieve relevant context for LLM queries."""

    def __init__(self):
        """Initialize the context retriever."""
        self.vector_store = get_vector_store()

    def retrieve_context(
        self,
        query: str,
        intent: ClassifiedIntent,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Retrieve all relevant context for a query.

        Args:
            query: User's query
            intent: Classified intent
            session_id: Optional session ID for conversation history

        Returns:
            Dict containing all relevant context
        """
        context = {
            'user_profile': self._get_user_profile(),
            'baselines': get_user_baselines(),
        }

        # Get data based on date scope
        if intent.date_scope:
            start_date, end_date = intent.date_scope
            if start_date == end_date:
                context['relevant_data'] = get_health_data_for_date(start_date)
            else:
                context['relevant_data'] = get_health_data_range(start_date, end_date)
        else:
            # Default to last 7 days
            end_date = date.today()
            start_date = end_date - timedelta(days=7)
            context['relevant_data'] = get_health_data_range(start_date, end_date)

        # Get similar cases from vector store
        context['similar_cases'] = self.vector_store.search_similar_days(query, n_results=3)

        # Get conversation history if session provided
        if session_id:
            context['conversation_history'] = get_recent_conversations(session_id, limit=5)

        # Add intent-specific context
        context.update(self._get_intent_specific_context(intent))

        return context

    def _get_user_profile(self) -> Dict[str, Any]:
        """Get the current user profile."""
        return {
            'name': user_profile.name,
            'bp_goal': user_profile.bp_goal,
            'sleep_goal': user_profile.sleep_goal,
            'steps_goal': user_profile.steps_goal,
            'vo2_max_goal': user_profile.vo2_max_goal
        }

    def _get_intent_specific_context(self, intent: ClassifiedIntent) -> Dict[str, Any]:
        """Get additional context based on intent type."""
        additional = {}

        if intent.intent_type == IntentType.TREND:
            # Get longer historical data for trends
            end_date = date.today()
            start_date = end_date - timedelta(days=30)
            additional['trend_data'] = get_health_data_range(start_date, end_date)

        elif intent.intent_type == IntentType.COMPARISON:
            # Get comparison groups
            additional['weekday_data'] = self._get_weekday_data()
            additional['weekend_data'] = self._get_weekend_data()

        elif intent.intent_type == IntentType.PREDICTION:
            # Get recent data for prediction context
            end_date = date.today()
            start_date = end_date - timedelta(days=14)
            additional['recent_history'] = get_health_data_range(start_date, end_date)

        return additional

    def _get_weekday_data(self) -> list:
        """Get recent weekday data."""
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        all_data = get_health_data_range(start_date, end_date)

        return [
            d for d in all_data
            if date.fromisoformat(d['date']).weekday() < 5
        ]

    def _get_weekend_data(self) -> list:
        """Get recent weekend data."""
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        all_data = get_health_data_range(start_date, end_date)

        return [
            d for d in all_data
            if date.fromisoformat(d['date']).weekday() >= 5
        ]
