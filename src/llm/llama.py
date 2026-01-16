"""
Local Llama integration for privacy-sensitive queries and cost savings.
"""
from typing import Dict, Any, List, Optional
import subprocess
import json


class LlamaClient:
    """Client for local Llama model interactions via Ollama."""

    def __init__(self, model_name: str = "llama3.1:8b"):
        """Initialize the Llama client."""
        self.model = model_name
        self._check_ollama()

    def _check_ollama(self) -> bool:
        """Check if Ollama is installed and the model is available."""
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                return False
            # Check if our specific model (with tag) is in the list
            # Output format: "llama3.1:8b    46e0c10c039e    4.9 GB..."
            for line in result.stdout.strip().split('\n'):
                if line.startswith(self.model):
                    return True
            return False
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    def generate_response(
        self,
        system_prompt: str,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        max_tokens: int = 2048
    ) -> Dict[str, Any]:
        """
        Generate a response using local Llama model.

        Args:
            system_prompt: System instructions
            user_message: User's query
            conversation_history: Optional list of prior messages
            max_tokens: Maximum tokens in response

        Returns:
            Dict with response text and model info
        """
        # Build the full prompt
        full_prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
{system_prompt}<|eot_id|>"""

        if conversation_history:
            for msg in conversation_history:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                full_prompt += f"""<|start_header_id|>{role}<|end_header_id|>
{content}<|eot_id|>"""

        full_prompt += f"""<|start_header_id|>user<|end_header_id|>
{user_message}<|eot_id|><|start_header_id|>assistant<|end_header_id|>"""

        try:
            # Call Ollama
            result = subprocess.run(
                ["ollama", "run", self.model, full_prompt],
                capture_output=True,
                text=True,
                timeout=120
            )

            response_text = result.stdout.strip()

            return {
                "response": response_text,
                "model": self.model,
                "input_tokens": len(full_prompt.split()),  # Approximate
                "output_tokens": len(response_text.split()),
                "total_tokens": len(full_prompt.split()) + len(response_text.split())
            }

        except subprocess.TimeoutExpired:
            return {
                "response": "Request timed out. Please try a simpler query.",
                "model": self.model,
                "error": "timeout"
            }
        except Exception as e:
            return {
                "response": f"Error: {str(e)}",
                "model": self.model,
                "error": str(e)
            }

    def is_available(self) -> bool:
        """Check if the Llama model is available."""
        return self._check_ollama()
