"""
Intent classification for user queries.
"""
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Tuple
from datetime import date, datetime, timedelta
import re


class IntentType(Enum):
    """Types of user intents."""
    DATA_LOOKUP = "data_lookup"  # "What was my BP yesterday?"
    EXPLANATION = "explanation"  # "Why was my BP high?"
    PREDICTION = "prediction"  # "What will my BP be tomorrow?"
    SCENARIO = "scenario"  # "What if I sleep 8 hours?"
    RECOMMENDATION = "recommendation"  # "How can I lower my BP?"
    TREND = "trend"  # "How has my BP changed this month?"
    COMPARISON = "comparison"  # "Compare my weekday vs weekend BP"
    GENERAL = "general"  # General health questions


@dataclass
class ClassifiedIntent:
    """Result of intent classification."""
    intent_type: IntentType
    confidence: float
    date_scope: Optional[Tuple[date, date]] = None
    entities: dict = None

    def __post_init__(self):
        if self.entities is None:
            self.entities = {}


class IntentClassifier:
    """Classify user queries into intent types."""

    def __init__(self):
        """Initialize the intent classifier."""
        # Intent patterns (regex-based for MVP)
        self.patterns = {
            IntentType.DATA_LOOKUP: [
                r'what was my (bp|blood pressure|sleep|steps)',
                r'show me my',
                r'my (bp|blood pressure) on',
                r'how much did i (sleep|walk)',
                r'(sleep|steps|bp|heart rate) data',
            ],
            IntentType.EXPLANATION: [
                r'why (was|is|did)',
                r'what caused',
                r'explain',
                r'reason for',
            ],
            IntentType.PREDICTION: [
                r'what will',
                r'predict',
                r'forecast',
                r'expect',
            ],
            IntentType.SCENARIO: [
                r'what if',
                r'if i (sleep|exercise|walk)',
                r'hypothetically',
                r'scenario',
            ],
            IntentType.RECOMMENDATION: [
                r'how (can|do|should) i',
                r'recommend',
                r'suggest',
                r'tips for',
                r'advice',
            ],
            IntentType.TREND: [
                r'trend',
                r'over (time|the past)',
                r'changed',
                r'progress',
            ],
            IntentType.COMPARISON: [
                r'compare',
                r'vs',
                r'versus',
                r'difference between',
            ],
        }

        # Date extraction patterns
        self.date_patterns = {
            'yesterday': lambda: date.today() - timedelta(days=1),
            'today': lambda: date.today(),
            'last week': lambda: (date.today() - timedelta(days=7), date.today()),
            'this week': lambda: (date.today() - timedelta(days=date.today().weekday()), date.today()),
            'last month': lambda: (date.today() - timedelta(days=30), date.today()),
        }

    def classify(self, query: str) -> ClassifiedIntent:
        """
        Classify a user query.

        Args:
            query: User's natural language query

        Returns:
            ClassifiedIntent with type, confidence, and extracted entities
        """
        query_lower = query.lower()

        # Find matching intent
        best_intent = IntentType.GENERAL
        best_confidence = 0.5

        for intent_type, patterns in self.patterns.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    best_intent = intent_type
                    best_confidence = 0.85
                    break
            if best_confidence > 0.5:
                break

        # Extract date scope
        date_scope = self._extract_date_scope(query_lower)

        # Extract entities
        entities = self._extract_entities(query_lower)

        return ClassifiedIntent(
            intent_type=best_intent,
            confidence=best_confidence,
            date_scope=date_scope,
            entities=entities
        )

    def _extract_date_scope(self, query: str) -> Optional[Tuple[date, date]]:
        """Extract date range from query."""
        for pattern, date_fn in self.date_patterns.items():
            if pattern in query:
                result = date_fn()
                if isinstance(result, tuple):
                    return result
                else:
                    return (result, result)

        # Try to find specific date mentions (e.g., "January 10")
        date_match = re.search(r'(\w+ \d{1,2}(?:st|nd|rd|th)?)', query)
        if date_match:
            try:
                parsed = datetime.strptime(
                    date_match.group(1).replace('st', '').replace('nd', '').replace('rd', '').replace('th', ''),
                    '%B %d'
                ).replace(year=date.today().year)
                return (parsed.date(), parsed.date())
            except ValueError:
                pass

        return None

    def _extract_entities(self, query: str) -> dict:
        """Extract relevant entities from query."""
        entities = {}

        # Extract metric types
        metrics = ['bp', 'blood pressure', 'sleep', 'steps', 'vo2', 'heart rate', 'hrv']
        for metric in metrics:
            if metric in query:
                entities['metric'] = metric.replace('blood pressure', 'bp')
                break

        # Extract numeric values
        numbers = re.findall(r'\b(\d+(?:\.\d+)?)\b', query)
        if numbers:
            entities['numbers'] = [float(n) for n in numbers]

        return entities
