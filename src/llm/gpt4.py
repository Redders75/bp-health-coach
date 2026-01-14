"""
GPT-4 API integration for validation and code generation.
"""
from typing import Dict, Any, List, Optional
from openai import OpenAI

from config.settings import OPENAI_API_KEY, llm_config


class GPT4Client:
    """Client for GPT-4 API interactions."""

    def __init__(self):
        """Initialize the GPT-4 client."""
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY environment variable not set")

        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.model = llm_config.gpt4_model

    def generate_response(
        self,
        system_prompt: str,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        max_tokens: int = None,
        json_mode: bool = False
    ) -> Dict[str, Any]:
        """
        Generate a response using GPT-4.

        Args:
            system_prompt: System instructions
            user_message: User's query
            conversation_history: Optional list of prior messages
            max_tokens: Maximum tokens in response
            json_mode: Whether to force JSON output

        Returns:
            Dict with response text, tokens used, and model info
        """
        if max_tokens is None:
            max_tokens = llm_config.max_tokens_per_query

        # Build messages
        messages = [{"role": "system", "content": system_prompt}]
        if conversation_history:
            messages.extend(conversation_history)
        messages.append({"role": "user", "content": user_message})

        # Set response format
        response_format = {"type": "json_object"} if json_mode else None

        # Call GPT-4 API
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens,
            response_format=response_format
        )

        # Extract response
        choice = response.choices[0]

        return {
            "response": choice.message.content,
            "model": self.model,
            "input_tokens": response.usage.prompt_tokens,
            "output_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens
        }

    def validate_response(
        self,
        original_response: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate a response from another LLM.

        Args:
            original_response: Response to validate
            context: Original context and data

        Returns:
            Validation result with corrections if needed
        """
        system_prompt = """You are a medical accuracy validator.
Check the following health advice for:
1. Factual accuracy against provided data
2. Appropriate medical disclaimers
3. Actionable and safe recommendations

Respond in JSON with:
- "valid": boolean
- "issues": list of any problems found
- "corrections": suggested corrections if any"""

        user_message = f"""RESPONSE TO VALIDATE:
{original_response}

ORIGINAL DATA:
{context}"""

        result = self.generate_response(
            system_prompt,
            user_message,
            json_mode=True
        )

        return result
