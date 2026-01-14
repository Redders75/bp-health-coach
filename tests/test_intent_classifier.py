"""
Tests for the intent classifier.
"""
import pytest
from datetime import date, timedelta

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.orchestration.intent_classifier import IntentClassifier, IntentType


@pytest.fixture
def classifier():
    return IntentClassifier()


class TestIntentClassifier:
    """Tests for IntentClassifier."""

    def test_data_lookup_intent(self, classifier):
        """Test classification of data lookup queries."""
        queries = [
            "What was my BP yesterday?",
            "Show me my sleep data",
            "How much did I walk last week?",
        ]

        for query in queries:
            result = classifier.classify(query)
            assert result.intent_type == IntentType.DATA_LOOKUP
            assert result.confidence >= 0.8

    def test_explanation_intent(self, classifier):
        """Test classification of explanation queries."""
        queries = [
            "Why was my BP high yesterday?",
            "What caused my poor sleep?",
            "Explain my elevated readings",
        ]

        for query in queries:
            result = classifier.classify(query)
            assert result.intent_type == IntentType.EXPLANATION

    def test_prediction_intent(self, classifier):
        """Test classification of prediction queries."""
        queries = [
            "What will my BP be tomorrow?",
            "Predict my readings for next week",
            "What should I expect?",
        ]

        for query in queries:
            result = classifier.classify(query)
            assert result.intent_type == IntentType.PREDICTION

    def test_scenario_intent(self, classifier):
        """Test classification of scenario queries."""
        queries = [
            "What if I sleep 8 hours?",
            "If I exercise more, what happens?",
            "Hypothetically, with better VO2...",
        ]

        for query in queries:
            result = classifier.classify(query)
            assert result.intent_type == IntentType.SCENARIO

    def test_date_extraction_yesterday(self, classifier):
        """Test extraction of 'yesterday' date."""
        result = classifier.classify("What was my BP yesterday?")

        assert result.date_scope is not None
        expected = date.today() - timedelta(days=1)
        assert result.date_scope[0] == expected

    def test_date_extraction_last_week(self, classifier):
        """Test extraction of 'last week' date range."""
        result = classifier.classify("Show me last week's data")

        assert result.date_scope is not None
        assert result.date_scope[0] == date.today() - timedelta(days=7)
        assert result.date_scope[1] == date.today()

    def test_entity_extraction(self, classifier):
        """Test extraction of metric entities."""
        result = classifier.classify("What was my BP yesterday?")
        assert result.entities.get('metric') == 'bp'

        result = classifier.classify("How was my sleep last night?")
        assert result.entities.get('metric') == 'sleep'
