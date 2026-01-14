"""
LLM Router for intelligent model selection.
"""
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, Optional

from src.llm.claude import ClaudeClient
from src.llm.gpt4 import GPT4Client
from src.llm.llama import LlamaClient


class QueryComplexity(Enum):
    """Query complexity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class PrivacySensitivity(Enum):
    """Privacy sensitivity levels."""
    PUBLIC = "public"
    PRIVATE = "private"
    SENSITIVE = "sensitive"


@dataclass
class QueryMetadata:
    """Metadata about a query for routing decisions."""
    complexity: QueryComplexity
    privacy: PrivacySensitivity
    requires_code: bool = False
    requires_medical_grounding: bool = False


class LLMRouter:
    """Route queries to the appropriate LLM based on requirements."""

    def __init__(self, cost_mode: bool = True):
        """
        Initialize the LLM router.

        Args:
            cost_mode: If True, prefer cheaper models when possible
        """
        self.cost_mode = cost_mode
        self._claude: Optional[ClaudeClient] = None
        self._gpt4: Optional[GPT4Client] = None
        self._llama: Optional[LlamaClient] = None

    @property
    def claude(self) -> ClaudeClient:
        """Lazy-load Claude client."""
        if self._claude is None:
            self._claude = ClaudeClient()
        return self._claude

    @property
    def gpt4(self) -> GPT4Client:
        """Lazy-load GPT-4 client."""
        if self._gpt4 is None:
            self._gpt4 = GPT4Client()
        return self._gpt4

    @property
    def llama(self) -> LlamaClient:
        """Lazy-load Llama client."""
        if self._llama is None:
            self._llama = LlamaClient()
        return self._llama

    def select_model(self, metadata: QueryMetadata) -> str:
        """
        Select the appropriate model based on query metadata.

        Args:
            metadata: Query metadata for routing decision

        Returns:
            Model name: 'claude', 'gpt4', or 'llama'
        """
        # Privacy override - sensitive queries stay local
        if metadata.privacy == PrivacySensitivity.SENSITIVE:
            return 'llama'

        # Code generation goes to GPT-4
        if metadata.requires_code:
            return 'gpt4'

        # Complexity-based routing
        if metadata.complexity == QueryComplexity.HIGH:
            return 'claude'
        elif metadata.complexity == QueryComplexity.MEDIUM:
            return 'gpt4' if not self.cost_mode else 'llama'
        else:
            return 'llama'  # Simple queries to local model

    def classify_query(self, query: str) -> QueryMetadata:
        """
        Classify a query to determine routing.

        Args:
            query: User's query text

        Returns:
            QueryMetadata for routing decision
        """
        query_lower = query.lower()

        # Determine privacy sensitivity
        privacy = PrivacySensitivity.PUBLIC
        sensitive_terms = ['medication', 'drug', 'mental', 'anxiety', 'depression']
        private_terms = ['doctor', 'prescription', 'diagnosis']

        if any(term in query_lower for term in sensitive_terms):
            privacy = PrivacySensitivity.SENSITIVE
        elif any(term in query_lower for term in private_terms):
            privacy = PrivacySensitivity.PRIVATE

        # Determine complexity
        complexity = QueryComplexity.LOW
        high_complexity = ['why', 'explain', 'analyze', 'what if', 'predict', 'recommend']
        medium_complexity = ['how', 'compare', 'trend', 'pattern']

        if any(term in query_lower for term in high_complexity):
            complexity = QueryComplexity.HIGH
        elif any(term in query_lower for term in medium_complexity):
            complexity = QueryComplexity.MEDIUM

        # Check for code requirements
        requires_code = 'code' in query_lower or 'script' in query_lower

        return QueryMetadata(
            complexity=complexity,
            privacy=privacy,
            requires_code=requires_code
        )

    def route_query(
        self,
        query: str,
        system_prompt: str,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Route a query to the appropriate model and get response.

        Args:
            query: User's query
            system_prompt: System instructions
            context: Optional context data

        Returns:
            Response dict with model info
        """
        metadata = self.classify_query(query)
        model_name = self.select_model(metadata)

        # Check if Llama is available, fall back to Claude if not
        if model_name == 'llama' and not self.llama.is_available():
            model_name = 'claude'

        # Add context to query if provided
        full_query = query
        if context:
            full_query = f"{query}\n\nContext:\n{context}"

        # Route to selected model
        if model_name == 'claude':
            result = self.claude.generate_response(system_prompt, full_query)
        elif model_name == 'gpt4':
            result = self.gpt4.generate_response(system_prompt, full_query)
        else:  # llama
            result = self.llama.generate_response(system_prompt, full_query)

        result['routed_model'] = model_name
        result['metadata'] = {
            'complexity': metadata.complexity.value,
            'privacy': metadata.privacy.value
        }

        return result
