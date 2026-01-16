"""
Conversation management for multi-turn interactions.
"""
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

from src.data.database import save_conversation, get_recent_conversations
from src.orchestration.intent_classifier import IntentClassifier, ClassifiedIntent
from src.orchestration.context_retrieval import ContextRetriever
from src.llm.router import LLMRouter


class ConversationManager:
    """Manage multi-turn conversations with context."""

    def __init__(self, session_id: Optional[str] = None):
        """
        Initialize the conversation manager.

        Args:
            session_id: Optional existing session ID
        """
        self.session_id = session_id or str(uuid.uuid4())
        self.intent_classifier = IntentClassifier()
        self.context_retriever = ContextRetriever()
        self.llm_router = LLMRouter()

        # In-memory conversation buffer
        self.messages: List[Dict[str, str]] = []

    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process a user query and generate a response.

        Args:
            query: User's natural language query

        Returns:
            Dict with response and metadata
        """
        # Classify intent
        intent = self.intent_classifier.classify(query)

        # Retrieve context
        context = self.context_retriever.retrieve_context(
            query, intent, self.session_id
        )

        # Build system prompt
        system_prompt = self._build_system_prompt(context)

        # Route to LLM and get response
        result = self.llm_router.route_query(query, system_prompt, context)

        response = result.get('response', '')

        # Save to conversation history
        self._save_turn(query, response, result, intent)

        return {
            'response': response,
            'session_id': self.session_id,
            'intent': intent.intent_type.value,
            'confidence': intent.confidence,
            'model_used': result.get('routed_model'),
            'tokens': result.get('total_tokens', 0)
        }

    def _build_system_prompt(self, context: Dict[str, Any]) -> str:
        """Build the system prompt with user context."""
        profile = context.get('user_profile', {})
        baselines = context.get('baselines', {})

        # Format baseline values, handling None
        avg_systolic = baselines.get('avg_systolic')
        avg_sleep = baselines.get('avg_sleep')
        avg_steps = baselines.get('avg_steps')

        systolic_str = f"{avg_systolic:.0f}" if avg_systolic else "N/A"
        sleep_str = f"{avg_sleep:.1f}" if avg_sleep else "N/A"
        steps_str = f"{avg_steps:,.0f}" if avg_steps else "N/A"

        return f"""You are an AI health coach for {profile.get('name', 'the user')}.

USER PROFILE:
- BP Goal: <{profile.get('bp_goal', 130)} mmHg
- Sleep Goal: {profile.get('sleep_goal', 7)} hours
- Steps Goal: {profile.get('steps_goal', 10000):,} steps
- VO2 Max Goal: {profile.get('vo2_max_goal', 43)}

USER BASELINES (90-day averages):
- Average Systolic BP: {systolic_str} mmHg
- Average Sleep: {sleep_str} hours
- Average Steps: {steps_str}

KEY PATTERNS (from prior analysis):
- VO2 Max: r=-0.494 with BP (strongest factor)
- Sleep: r=-0.375 with BP
- Steps: r=-0.187 with BP
- Weekend BP: +4.8 mmHg higher
- Sleep <6hrs: +6.2 mmHg

INSTRUCTIONS:
1. Provide personalized, evidence-based responses
2. Reference the user's actual data and patterns
3. Always report blood pressure as Systolic/Diastolic (e.g., "134/84 mmHg")
4. Give specific, actionable recommendations
5. Acknowledge uncertainty when appropriate
6. Never diagnose or prescribe - suggest consulting a doctor for concerns
7. Be encouraging but realistic

Keep responses concise but informative."""

    def _save_turn(
        self,
        query: str,
        response: str,
        result: Dict[str, Any],
        intent: ClassifiedIntent
    ) -> None:
        """Save a conversation turn."""
        # Update in-memory buffer
        self.messages.append({"role": "user", "content": query})
        self.messages.append({"role": "assistant", "content": response})

        # Keep only recent messages
        if len(self.messages) > 10:
            self.messages = self.messages[-10:]

        # Calculate approximate cost
        tokens = result.get('total_tokens', 0)
        model = result.get('routed_model', '')

        if model == 'claude':
            cost = tokens * 0.000015  # Approximate
        elif model == 'gpt4':
            cost = tokens * 0.00003
        else:
            cost = 0.0

        # Save to database
        save_conversation(
            session_id=self.session_id,
            user_query=query,
            assistant_response=response,
            llm_model=model,
            tokens_used=tokens,
            cost_usd=cost,
            intent_type=intent.intent_type.value,
            confidence=intent.confidence
        )

    def get_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent conversation history."""
        return get_recent_conversations(self.session_id, limit)

    def clear_session(self) -> None:
        """Clear the current session and start fresh."""
        self.session_id = str(uuid.uuid4())
        self.messages = []
