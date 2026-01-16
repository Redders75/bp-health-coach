"""
Prediction and scenario analysis utilities.
"""
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass

from src.models.ml_models import BPPredictor


@dataclass
class ScenarioResult:
    """Result of a what-if scenario analysis."""
    current_systolic: float
    current_diastolic: float
    predicted_systolic: float
    predicted_diastolic: float
    bp_change: float  # Systolic change
    diastolic_change: float
    confidence_interval: Tuple[float, float]
    timeline_weeks: int
    feasibility: str
    recommendations: List[str]

    # Backwards compatibility properties
    @property
    def current_bp(self) -> float:
        return self.current_systolic

    @property
    def predicted_bp(self) -> float:
        return self.predicted_systolic


class ScenarioAnalyzer:
    """Analyze what-if scenarios for health changes."""

    def __init__(self):
        self.predictor = BPPredictor()

        # Impact coefficients (from prior analysis)
        self.impact_coefficients = {
            'vo2_max': -1.96,  # mmHg per unit increase
            'sleep_hours': -3.1,  # mmHg per hour increase
            'steps': -0.0003,  # mmHg per step increase
            'sleep_efficiency_pct': -0.2,  # mmHg per % increase
        }

    def analyze_scenario(
        self,
        current_state: Dict[str, float],
        hypothetical_state: Dict[str, float],
        current_systolic: float,
        current_diastolic: float = None
    ) -> ScenarioResult:
        """
        Analyze the impact of changing health metrics.

        Args:
            current_state: Current health metrics
            hypothetical_state: Proposed health metrics
            current_systolic: Current systolic blood pressure
            current_diastolic: Current diastolic blood pressure (estimated if not provided)

        Returns:
            ScenarioResult with predictions and recommendations
        """
        # Estimate diastolic if not provided (typical ratio ~0.65)
        if current_diastolic is None:
            current_diastolic = current_systolic * 0.65

        # Calculate expected systolic BP change
        systolic_change = 0.0
        for metric, coefficient in self.impact_coefficients.items():
            if metric in hypothetical_state and metric in current_state:
                delta = hypothetical_state[metric] - current_state[metric]
                systolic_change += delta * coefficient

        predicted_systolic = current_systolic + systolic_change

        # Diastolic typically changes proportionally (about 50% of systolic change)
        diastolic_change = systolic_change * 0.5
        predicted_diastolic = current_diastolic + diastolic_change

        # Determine confidence interval (for systolic)
        ci_low = predicted_systolic - 5
        ci_high = predicted_systolic + 5

        # Estimate timeline and feasibility
        timeline, feasibility = self._estimate_feasibility(
            current_state, hypothetical_state
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(
            current_state, hypothetical_state
        )

        return ScenarioResult(
            current_systolic=current_systolic,
            current_diastolic=current_diastolic,
            predicted_systolic=predicted_systolic,
            predicted_diastolic=predicted_diastolic,
            bp_change=systolic_change,
            diastolic_change=diastolic_change,
            confidence_interval=(ci_low, ci_high),
            timeline_weeks=timeline,
            feasibility=feasibility,
            recommendations=recommendations
        )

    def _estimate_feasibility(
        self,
        current: Dict[str, float],
        target: Dict[str, float]
    ) -> Tuple[int, str]:
        """Estimate timeline and feasibility of changes."""
        # Simplified feasibility estimation
        vo2_change = target.get('vo2_max', 0) - current.get('vo2_max', 0)

        if vo2_change > 5:
            return (12, "MODERATE")
        elif vo2_change > 2:
            return (6, "HIGH")
        else:
            return (4, "VERY HIGH")

    def _generate_recommendations(
        self,
        current: Dict[str, float],
        target: Dict[str, float]
    ) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []

        if target.get('vo2_max', 0) > current.get('vo2_max', 0):
            recommendations.append(
                "Increase cardio frequency to 4-5x per week"
            )
            recommendations.append(
                "Include 2 high-intensity interval sessions weekly"
            )

        if target.get('sleep_hours', 0) > current.get('sleep_hours', 0):
            recommendations.append(
                f"Target {target['sleep_hours']:.1f} hours of sleep nightly"
            )

        if target.get('steps', 0) > current.get('steps', 0):
            step_diff = target['steps'] - current['steps']
            recommendations.append(
                f"Add {step_diff:,} daily steps through walking breaks"
            )

        return recommendations
