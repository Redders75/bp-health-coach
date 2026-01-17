"""
Goal tracking and progress monitoring feature.

Tracks progress toward health goals and provides
projections for goal achievement.
"""
from datetime import date, datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
from statistics import mean, stdev

from src.data.database import get_health_data_range, get_user_baselines, get_connection
from config.settings import user_profile


class GoalStatus(Enum):
    """Status of goal progress."""
    ACHIEVED = "achieved"
    ON_TRACK = "on_track"
    AT_RISK = "at_risk"
    OFF_TRACK = "off_track"
    NOT_STARTED = "not_started"


@dataclass
class Goal:
    """Represents a health goal."""
    name: str
    metric: str
    current_value: float
    target_value: float
    baseline_value: float
    direction: str  # 'lower' or 'higher'
    unit: str
    start_date: date
    target_date: Optional[date] = None

    @property
    def progress_pct(self) -> float:
        """Calculate progress percentage toward goal."""
        if self.baseline_value == self.target_value:
            return 100.0

        total_change_needed = abs(self.target_value - self.baseline_value)
        change_achieved = abs(self.current_value - self.baseline_value)

        # Check if moving in right direction
        if self.direction == 'lower':
            if self.current_value > self.baseline_value:
                return 0.0  # Moving wrong direction
            change_achieved = self.baseline_value - self.current_value
        else:
            if self.current_value < self.baseline_value:
                return 0.0
            change_achieved = self.current_value - self.baseline_value

        progress = (change_achieved / total_change_needed) * 100
        return min(100.0, max(0.0, progress))

    @property
    def gap_to_goal(self) -> float:
        """Calculate gap remaining to goal."""
        return abs(self.current_value - self.target_value)

    @property
    def status(self) -> GoalStatus:
        """Determine current goal status."""
        if self.progress_pct >= 100:
            return GoalStatus.ACHIEVED

        # For goals with target dates, check pace
        if self.target_date:
            days_elapsed = (date.today() - self.start_date).days
            days_total = (self.target_date - self.start_date).days
            expected_progress = (days_elapsed / days_total) * 100 if days_total > 0 else 0

            if self.progress_pct >= expected_progress:
                return GoalStatus.ON_TRACK
            elif self.progress_pct >= expected_progress * 0.7:
                return GoalStatus.AT_RISK
            else:
                return GoalStatus.OFF_TRACK

        # Without target date, just check if making progress
        if self.progress_pct > 0:
            return GoalStatus.ON_TRACK
        return GoalStatus.NOT_STARTED


class GoalTracker:
    """Track progress toward health goals."""

    def __init__(self):
        """Initialize the goal tracker."""
        self._init_goals_table()
        self.baselines = get_user_baselines()

    def _init_goals_table(self):
        """Initialize goals table in database."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS goals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    metric TEXT NOT NULL,
                    target_value REAL NOT NULL,
                    baseline_value REAL NOT NULL,
                    direction TEXT NOT NULL,
                    unit TEXT NOT NULL,
                    start_date DATE NOT NULL,
                    target_date DATE,
                    achieved_date DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Goals history for tracking progress over time
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS goal_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    goal_id INTEGER,
                    date DATE NOT NULL,
                    value REAL NOT NULL,
                    progress_pct REAL,
                    FOREIGN KEY (goal_id) REFERENCES goals(id)
                )
            """)
            conn.commit()

    def get_default_goals(self) -> List[Goal]:
        """Get the default health goals based on user profile."""
        today = date.today()
        ninety_days_ago = today - timedelta(days=90)

        # Get current values from recent data
        recent_data = get_health_data_range(today - timedelta(days=7), today)
        current = self._calculate_current_values(recent_data)

        goals = []

        # BP Goal
        baseline_bp = self.baselines.get('avg_systolic') or 142
        goals.append(Goal(
            name="Blood Pressure",
            metric="systolic_mean",
            current_value=current.get('bp', baseline_bp),
            target_value=user_profile.bp_goal,
            baseline_value=baseline_bp,
            direction='lower',
            unit='mmHg',
            start_date=ninety_days_ago
        ))

        # VO2 Max Goal
        baseline_vo2 = self.baselines.get('avg_vo2_max') or 37
        goals.append(Goal(
            name="VO2 Max",
            metric="vo2_max",
            current_value=current.get('vo2_max', baseline_vo2),
            target_value=user_profile.vo2_max_goal,
            baseline_value=baseline_vo2,
            direction='higher',
            unit='mL/kg/min',
            start_date=ninety_days_ago
        ))

        # Sleep Goal
        baseline_sleep = self.baselines.get('avg_sleep') or 6.5
        goals.append(Goal(
            name="Sleep Duration",
            metric="sleep_hours",
            current_value=current.get('sleep', baseline_sleep),
            target_value=7.0,
            baseline_value=baseline_sleep,
            direction='higher',
            unit='hours',
            start_date=ninety_days_ago
        ))

        # Steps Goal
        baseline_steps = self.baselines.get('avg_steps') or 9000
        goals.append(Goal(
            name="Daily Steps",
            metric="steps",
            current_value=current.get('steps', baseline_steps),
            target_value=10000,
            baseline_value=baseline_steps,
            direction='higher',
            unit='steps',
            start_date=ninety_days_ago
        ))

        return goals

    def _calculate_current_values(self, recent_data: List[Dict]) -> Dict[str, float]:
        """Calculate current values from recent data."""
        if not recent_data:
            return {}

        values = {}

        bp_vals = [d['systolic_mean'] for d in recent_data if d.get('systolic_mean')]
        if bp_vals:
            values['bp'] = mean(bp_vals)

        vo2_vals = [d['vo2_max'] for d in recent_data if d.get('vo2_max')]
        if vo2_vals:
            values['vo2_max'] = vo2_vals[0]  # Use most recent

        sleep_vals = [d['sleep_hours'] for d in recent_data if d.get('sleep_hours')]
        if sleep_vals:
            values['sleep'] = mean(sleep_vals)

        steps_vals = [d['steps'] for d in recent_data if d.get('steps')]
        if steps_vals:
            values['steps'] = mean(steps_vals)

        return values

    def get_goal_dashboard(self) -> Dict[str, Any]:
        """
        Get a comprehensive goal tracking dashboard.

        Returns summary of all goals with progress and projections.
        """
        goals = self.get_default_goals()
        dashboard = {
            'goals': [],
            'overall_status': GoalStatus.ON_TRACK.value,
            'summary': {}
        }

        achieved_count = 0
        on_track_count = 0

        for goal in goals:
            goal_data = {
                'name': goal.name,
                'metric': goal.metric,
                'current': goal.current_value,
                'target': goal.target_value,
                'baseline': goal.baseline_value,
                'unit': goal.unit,
                'progress_pct': goal.progress_pct,
                'gap': goal.gap_to_goal,
                'status': goal.status.value,
                'trend': self._calculate_trend(goal.metric),
                'projection': self._project_achievement(goal)
            }
            dashboard['goals'].append(goal_data)

            if goal.status == GoalStatus.ACHIEVED:
                achieved_count += 1
            elif goal.status == GoalStatus.ON_TRACK:
                on_track_count += 1

        # Calculate overall status
        total = len(goals)
        if achieved_count == total:
            dashboard['overall_status'] = GoalStatus.ACHIEVED.value
        elif achieved_count + on_track_count >= total * 0.75:
            dashboard['overall_status'] = GoalStatus.ON_TRACK.value
        elif achieved_count + on_track_count >= total * 0.5:
            dashboard['overall_status'] = GoalStatus.AT_RISK.value
        else:
            dashboard['overall_status'] = GoalStatus.OFF_TRACK.value

        dashboard['summary'] = {
            'achieved': achieved_count,
            'on_track': on_track_count,
            'at_risk': total - achieved_count - on_track_count,
            'total': total
        }

        return dashboard

    def _calculate_trend(self, metric: str, days: int = 30) -> Dict[str, Any]:
        """Calculate trend for a specific metric."""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        data = get_health_data_range(start_date, end_date)

        if not data:
            return {'direction': 'stable', 'change': 0, 'confidence': 'low'}

        values = [(d['date'], d.get(metric)) for d in data if d.get(metric)]
        if len(values) < 5:
            return {'direction': 'stable', 'change': 0, 'confidence': 'low'}

        # Compare first half to second half
        mid = len(values) // 2
        first_half = [v[1] for v in values[mid:]]  # Older dates
        second_half = [v[1] for v in values[:mid]]  # Recent dates

        first_avg = mean(first_half)
        second_avg = mean(second_half)
        change = second_avg - first_avg

        # Determine direction
        if abs(change) < 1:
            direction = 'stable'
        elif change > 0:
            direction = 'increasing'
        else:
            direction = 'decreasing'

        return {
            'direction': direction,
            'change': change,
            'confidence': 'high' if len(values) >= 14 else 'medium'
        }

    def _project_achievement(self, goal: Goal) -> Dict[str, Any]:
        """Project when a goal might be achieved based on current trend."""
        if goal.status == GoalStatus.ACHIEVED:
            return {'status': 'achieved', 'weeks_remaining': 0}

        trend = self._calculate_trend(goal.metric)

        if trend['direction'] == 'stable' or trend['change'] == 0:
            return {
                'status': 'no_progress',
                'weeks_remaining': None,
                'message': 'No significant progress detected. Consider adjusting approach.'
            }

        # Check if moving in wrong direction
        moving_right = (goal.direction == 'lower' and trend['change'] < 0) or \
                       (goal.direction == 'higher' and trend['change'] > 0)

        if not moving_right:
            return {
                'status': 'regressing',
                'weeks_remaining': None,
                'message': 'Moving away from goal. Review recent habits.'
            }

        # Calculate weeks to goal at current rate
        gap = goal.gap_to_goal
        weekly_change = abs(trend['change']) * (7 / 30)  # Convert monthly to weekly

        if weekly_change > 0:
            weeks = gap / weekly_change
            if weeks <= 52:
                return {
                    'status': 'projected',
                    'weeks_remaining': round(weeks),
                    'message': f'At current rate, goal in ~{round(weeks)} weeks'
                }
            else:
                return {
                    'status': 'long_term',
                    'weeks_remaining': round(weeks),
                    'message': 'Goal is long-term. Consider more aggressive approach.'
                }

        return {'status': 'unknown', 'weeks_remaining': None}

    def get_goal_history(self, metric: str, days: int = 90) -> List[Dict]:
        """Get historical values for a metric to show progress over time."""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        data = get_health_data_range(start_date, end_date)

        history = []
        for d in sorted(data, key=lambda x: x['date']):
            if d.get(metric):
                history.append({
                    'date': d['date'],
                    'value': d[metric]
                })

        return history

    def get_recommendations_for_goal(self, goal_name: str) -> List[str]:
        """Get specific recommendations for improving a goal."""
        recommendations = {
            'Blood Pressure': [
                "Focus on VO2 Max improvement - your strongest BP predictor",
                "Maintain 7+ hours sleep consistently",
                "Aim for 10,000+ steps daily",
                "Reduce sodium intake to under 2,300mg/day",
                "Practice stress management techniques"
            ],
            'VO2 Max': [
                "Add 3-4 cardio sessions per week (30+ min each)",
                "Include 1-2 high-intensity interval sessions",
                "Gradually increase workout duration and intensity",
                "Track heart rate during exercise to optimize training zones",
                "Allow adequate recovery between intense sessions"
            ],
            'Sleep Duration': [
                "Set a consistent bedtime alarm",
                "Create a wind-down routine 30 min before bed",
                "Limit screen time in the evening",
                "Keep bedroom cool (65-68°F) and dark",
                "Avoid caffeine after 2 PM"
            ],
            'Daily Steps': [
                "Take a 20-minute walk after each meal",
                "Use stairs instead of elevators",
                "Park farther from destinations",
                "Set hourly movement reminders",
                "Consider a walking meeting or call"
            ]
        }

        return recommendations.get(goal_name, [
            "Stay consistent with your current healthy habits",
            "Track your progress regularly",
            "Celebrate small wins along the way"
        ])

    def format_dashboard_text(self) -> str:
        """Format the goal dashboard as readable text."""
        dashboard = self.get_goal_dashboard()

        output = """
╔══════════════════════════════════════════════════════════════╗
║                    GOAL TRACKING DASHBOARD                    ║
╚══════════════════════════════════════════════════════════════╝

"""
        # Overall status
        status_emoji = {
            'achieved': '🏆',
            'on_track': '✅',
            'at_risk': '⚠️',
            'off_track': '❌'
        }
        emoji = status_emoji.get(dashboard['overall_status'], '📊')
        output += f"Overall Status: {emoji} {dashboard['overall_status'].upper()}\n"
        output += f"Goals: {dashboard['summary']['achieved']}/{dashboard['summary']['total']} achieved, "
        output += f"{dashboard['summary']['on_track']} on track\n\n"

        output += "─" * 60 + "\n\n"

        # Individual goals
        for goal in dashboard['goals']:
            status_emoji_map = {
                'achieved': '🏆',
                'on_track': '✅',
                'at_risk': '⚠️',
                'off_track': '❌',
                'not_started': '○'
            }
            emoji = status_emoji_map.get(goal['status'], '○')

            output += f"{emoji} {goal['name']}\n"
            output += f"   Current: {goal['current']:.1f} {goal['unit']} → Target: {goal['target']:.1f} {goal['unit']}\n"

            # Progress bar
            progress = min(100, goal['progress_pct'])
            filled = int(progress / 5)
            bar = '█' * filled + '░' * (20 - filled)
            output += f"   Progress: [{bar}] {progress:.0f}%\n"

            # Trend
            trend = goal['trend']
            trend_arrow = {'increasing': '↑', 'decreasing': '↓', 'stable': '→'}
            output += f"   Trend: {trend_arrow.get(trend['direction'], '→')} {trend['direction']}"
            if trend['change'] != 0:
                output += f" ({trend['change']:+.1f}/month)"
            output += "\n"

            # Projection
            proj = goal['projection']
            if proj.get('weeks_remaining') is not None:
                output += f"   Projection: {proj['message']}\n"

            output += "\n"

        return output
