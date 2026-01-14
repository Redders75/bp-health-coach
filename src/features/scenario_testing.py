"""
What-if scenario testing feature.
"""
from typing import Dict, Any, Optional, List

from src.models.predictions import ScenarioAnalyzer, ScenarioResult
from src.data.database import get_user_baselines
from src.llm.claude import ClaudeClient


class ScenarioEngine:
    """Engine for what-if scenario analysis."""

    def __init__(self):
        """Initialize the scenario engine."""
        self.analyzer = ScenarioAnalyzer()
        self.claude = ClaudeClient()

    def test_scenario(
        self,
        changes: Dict[str, float],
        current_bp: Optional[float] = None
    ) -> ScenarioResult:
        """
        Test a hypothetical scenario.

        Args:
            changes: Dict of metric changes (e.g., {'vo2_max': 42})
            current_bp: Current BP (uses baseline if not provided)

        Returns:
            ScenarioResult with predictions
        """
        baselines = get_user_baselines()

        if current_bp is None:
            current_bp = baselines.get('avg_systolic') or 142

        # Build current state from baselines (use defaults if None)
        current_state = {
            'vo2_max': baselines.get('avg_vo2_max') or 37,
            'sleep_hours': baselines.get('avg_sleep') or 6.5,
            'steps': baselines.get('avg_steps') or 9000,
            'sleep_efficiency_pct': 80  # Default
        }

        # Build hypothetical state
        hypothetical_state = current_state.copy()
        hypothetical_state.update(changes)

        return self.analyzer.analyze_scenario(
            current_state, hypothetical_state, current_bp
        )

    def test_scenario_natural_language(self, query: str) -> str:
        """
        Test a scenario from natural language input.

        Args:
            query: Natural language scenario description

        Returns:
            Natural language response with analysis
        """
        # Parse the scenario using Claude
        result = self._parse_scenario(query)

        if not result.get('changes'):
            return "I couldn't understand the scenario. Please specify what you'd like to change (e.g., 'What if I improve my VO2 Max to 42?')"

        # Run the analysis
        scenario_result = self.test_scenario(result['changes'])

        # Format as natural language
        return self._format_scenario_result(scenario_result, result['changes'])

    def _parse_scenario(self, query: str) -> Dict[str, Any]:
        """Parse a natural language scenario."""
        # Simple keyword-based parsing for MVP
        changes = {}
        query_lower = query.lower()

        import re

        # VO2 Max
        vo2_match = re.search(r'vo2\s*(?:max)?\s*(?:to|of|at)?\s*(\d+)', query_lower)
        if vo2_match:
            changes['vo2_max'] = float(vo2_match.group(1))

        # Sleep
        sleep_match = re.search(r'sleep\s*(\d+(?:\.\d+)?)\s*hours?', query_lower)
        if sleep_match:
            changes['sleep_hours'] = float(sleep_match.group(1))

        # Steps
        steps_match = re.search(r'(\d{1,2})k?\s*steps', query_lower)
        if steps_match:
            steps = int(steps_match.group(1))
            if 'k' in query_lower or steps < 100:
                steps *= 1000
            changes['steps'] = steps

        return {'changes': changes}

    def _format_scenario_result(
        self,
        result: ScenarioResult,
        changes: Dict[str, float]
    ) -> str:
        """Format scenario result as natural language."""
        changes_str = ", ".join(
            f"{k.replace('_', ' ').title()}: {v}" for k, v in changes.items()
        )

        response = f"""SCENARIO ANALYSIS: {changes_str}

PREDICTED IMPACT:
- BP reduction: {result.bp_change:.1f} mmHg
- Your {result.current_bp:.0f} mmHg → predicted {result.predicted_bp:.0f} mmHg
- 95% confidence interval: {result.confidence_interval[0]:.0f} to {result.confidence_interval[1]:.0f} mmHg

TIMELINE:
- Estimated achievement: {result.timeline_weeks} weeks
- Effects typically show after 2-3 weeks

FEASIBILITY: {result.feasibility}

RECOMMENDATIONS:
"""
        for i, rec in enumerate(result.recommendations, 1):
            response += f"{i}. {rec}\n"

        return response

    def compare_scenarios(
        self,
        scenarios: List[Dict[str, float]]
    ) -> List[ScenarioResult]:
        """
        Compare multiple scenarios.

        Args:
            scenarios: List of change dictionaries

        Returns:
            List of ScenarioResults
        """
        return [self.test_scenario(changes) for changes in scenarios]
