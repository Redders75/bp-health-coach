"""
Claude API integration for primary reasoning.
"""
from typing import Dict, Any, List, Optional
import anthropic

from config.settings import ANTHROPIC_API_KEY, llm_config


class ClaudeClient:
    """Client for Claude API interactions."""

    def __init__(self):
        """Initialize the Claude client."""
        if not ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")

        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        self.model = llm_config.claude_model

    def generate_response(
        self,
        system_prompt: str,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        max_tokens: int = None
    ) -> Dict[str, Any]:
        """
        Generate a response using Claude.

        Args:
            system_prompt: System instructions for Claude
            user_message: User's query
            conversation_history: Optional list of prior messages
            max_tokens: Maximum tokens in response

        Returns:
            Dict with response text, tokens used, and model info
        """
        if max_tokens is None:
            max_tokens = llm_config.max_tokens_per_query

        # Build messages
        messages = []
        if conversation_history:
            messages.extend(conversation_history)
        messages.append({"role": "user", "content": user_message})

        # Call Claude API
        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=messages
        )

        # Extract response
        response_text = response.content[0].text

        return {
            "response": response_text,
            "model": self.model,
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
            "total_tokens": response.usage.input_tokens + response.usage.output_tokens
        }

    def analyze_health_query(
        self,
        query: str,
        context: Dict[str, Any],
        user_profile: Dict[str, Any]
    ) -> str:
        """
        Analyze a health-related query with context.

        Args:
            query: User's health question
            context: Retrieved health data context
            user_profile: User's profile and baselines

        Returns:
            Natural language response
        """
        system_prompt = self._build_health_system_prompt(user_profile)
        user_message = self._build_context_message(query, context)

        result = self.generate_response(system_prompt, user_message)
        return result["response"]

    def _build_health_system_prompt(self, user_profile: Dict[str, Any]) -> str:
        """Build the system prompt for health analysis."""
        return f"""You are an AI health coach analyzing blood pressure data for {user_profile.get('name', 'the user')}.

USER PROFILE:
- Average BP: {user_profile.get('avg_systolic', 142)} mmHg
- Goal BP: {user_profile.get('bp_goal', 130)} mmHg
- Top factors affecting BP: VO2 Max (r=-0.494), Sleep (r=-0.375), Steps (r=-0.187)
- Known patterns: Weekend BP +4.8 mmHg, Sleep <6hrs = +6.2 mmHg

INSTRUCTIONS:
1. Provide evidence-based responses using the user's actual data
2. Identify top contributing factors with quantitative evidence
3. Compare to the user's patterns (not population averages)
4. Give specific, actionable recommendations
5. Acknowledge uncertainty when data is ambiguous
6. Never provide medical diagnosis or prescribe treatment
7. Recommend consulting a doctor for concerning patterns

Always cite specific data points to support your analysis."""

    def _build_context_message(self, query: str, context: Dict[str, Any]) -> str:
        """Build the context-enriched user message."""
        parts = [f"QUERY: {query}\n"]

        if context.get('relevant_data'):
            parts.append("RELEVANT DATA:")
            parts.append(str(context['relevant_data']))
            parts.append("")

        if context.get('similar_cases'):
            parts.append("SIMILAR PAST DAYS:")
            for case in context['similar_cases'][:3]:
                parts.append(f"- {case.get('summary', str(case))}")
            parts.append("")

        if context.get('baselines'):
            parts.append("USER BASELINES:")
            parts.append(str(context['baselines']))

        return "\n".join(parts)
