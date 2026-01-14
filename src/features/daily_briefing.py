"""
Daily briefing generation feature.
"""
from datetime import date, timedelta
from typing import Dict, Any, Optional

from src.data.database import get_health_data_for_date, get_health_data_range, get_user_baselines
from src.models.ml_models import BPPredictor
from src.llm.claude import ClaudeClient
from config.settings import user_profile


class DailyBriefingGenerator:
    """Generate personalized daily health briefings."""

    def __init__(self):
        """Initialize the briefing generator."""
        self.predictor = BPPredictor()
        self.claude = ClaudeClient()

    def generate_briefing(self, target_date: Optional[date] = None) -> str:
        """
        Generate a daily health briefing.

        Args:
            target_date: Date to generate briefing for (defaults to today)

        Returns:
            Formatted briefing string
        """
        if target_date is None:
            target_date = date.today()

        yesterday = target_date - timedelta(days=1)

        # Get yesterday's data
        yesterday_data = get_health_data_for_date(yesterday)

        # Get recent trend data
        week_ago = target_date - timedelta(days=7)
        recent_data = get_health_data_range(week_ago, yesterday)

        # Get baselines
        baselines = get_user_baselines()

        # Generate prediction for today
        prediction = self._generate_prediction(yesterday_data)

        # Build briefing
        briefing = self._compose_briefing(
            target_date,
            yesterday_data,
            recent_data,
            baselines,
            prediction
        )

        return briefing

    def _generate_prediction(self, recent_data: Optional[Dict]) -> Dict[str, Any]:
        """Generate BP prediction for today."""
        if not recent_data:
            return {
                'predicted_bp': 140,
                'confidence': 10,
                'main_factor': 'insufficient data'
            }

        features = {
            'sleep_hours': recent_data.get('sleep_hours', 7),
            'sleep_efficiency_pct': recent_data.get('sleep_efficiency_pct', 80),
            'steps': recent_data.get('steps', 8000),
            'vo2_max': recent_data.get('vo2_max', 37),
            'stress_score': recent_data.get('stress_score', 50),
            'hrv_mean': recent_data.get('hrv_mean', 30)
        }

        predicted, confidence = self.predictor.predict(features)

        # Determine main influencing factor
        importance = self.predictor.get_feature_importance()
        main_factor = max(importance, key=importance.get)

        return {
            'predicted_bp': predicted,
            'confidence': confidence,
            'main_factor': main_factor
        }

    def _compose_briefing(
        self,
        target_date: date,
        yesterday_data: Optional[Dict],
        recent_data: list,
        baselines: Dict,
        prediction: Dict
    ) -> str:
        """Compose the full briefing text."""
        date_str = target_date.strftime("%A, %B %d, %Y")

        if not yesterday_data:
            return f"""MORNING BRIEFING: {date_str}

No data available for yesterday. Please ensure your health data is synced.

Today's prediction is based on your historical averages.
Expected BP: {prediction['predicted_bp']:.0f} mmHg (±{prediction['confidence']:.0f})
"""

        # Extract yesterday's metrics
        bp = yesterday_data.get('systolic_mean', 'N/A')
        sleep = yesterday_data.get('sleep_hours', 0)
        sleep_eff = yesterday_data.get('sleep_efficiency_pct', 0)
        steps = yesterday_data.get('steps', 0)

        # Determine categories
        bp_category = self._categorize_bp(bp) if isinstance(bp, (int, float)) else 'unknown'
        sleep_quality = 'good' if sleep >= 7 else ('fair' if sleep >= 6 else 'poor')
        activity_level = 'active' if steps >= 10000 else ('moderate' if steps >= 5000 else 'low')

        # Generate recommendations
        recommendations = self._generate_recommendations(yesterday_data, baselines)

        briefing = f"""MORNING BRIEFING: {date_str}

YESTERDAY'S SUMMARY:
- BP: {bp} mmHg ({bp_category})
- Sleep: {sleep:.1f}hrs ({sleep_eff:.0f}% efficiency) - {sleep_quality}
- Activity: {steps:,} steps - {activity_level}

TODAY'S PREDICTION:
Expected BP: {prediction['predicted_bp']:.0f} mmHg (±{prediction['confidence']:.0f})
Key factor: {prediction['main_factor'].replace('_', ' ').title()}

RECOMMENDATIONS:
"""
        for i, rec in enumerate(recommendations[:3], 1):
            briefing += f"{i}. {rec}\n"

        # Add motivational message
        briefing += f"\n{self._get_motivational_message(yesterday_data, baselines)}"

        return briefing

    def _categorize_bp(self, systolic: float) -> str:
        """Categorize blood pressure reading."""
        if systolic < 120:
            return "normal"
        elif systolic < 130:
            return "elevated"
        elif systolic < 140:
            return "stage 1 hypertension"
        else:
            return "stage 2 hypertension"

    def _generate_recommendations(
        self,
        yesterday: Dict,
        baselines: Dict
    ) -> list:
        """Generate personalized recommendations."""
        recommendations = []

        sleep = yesterday.get('sleep_hours', 0)
        steps = yesterday.get('steps', 0)
        vo2 = yesterday.get('vo2_max', 0)

        if sleep < 7:
            recommendations.append(
                f"Prioritize sleep tonight - aim for 7+ hours (you got {sleep:.1f}hrs)"
            )

        if steps < 10000:
            gap = 10000 - steps
            recommendations.append(
                f"Add {gap:,} more steps today to hit your goal"
            )

        if vo2 and vo2 < user_profile.vo2_max_goal:
            recommendations.append(
                "Include cardio exercise to improve VO2 Max - your strongest BP factor"
            )

        if not recommendations:
            recommendations.append("Maintain your current healthy habits!")

        return recommendations

    def _get_motivational_message(self, yesterday: Dict, baselines: Dict) -> str:
        """Generate a motivational message based on performance."""
        bp = yesterday.get('systolic_mean', 999)
        avg_bp = baselines.get('avg_systolic', 142)

        if bp < avg_bp - 5:
            return "Great job! Your BP was below your average yesterday. Keep up the good work!"
        elif bp > avg_bp + 5:
            return "Yesterday was a tougher day for BP. Today is a fresh start!"
        else:
            return "Consistency is key. Every healthy choice adds up over time."
