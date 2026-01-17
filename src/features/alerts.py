"""
Real-time alert engine for health monitoring.

Detects patterns, anomalies, and achievements in health data
and generates appropriate alerts/notifications.
"""
from datetime import date, datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
from statistics import mean, stdev

from src.data.database import get_health_data_range, get_user_baselines, get_connection
from config.settings import user_profile


class AlertPriority(Enum):
    """Alert priority levels."""
    CRITICAL = "critical"      # Requires immediate attention
    WARNING = "warning"        # Should address soon
    INFO = "info"             # Good to know
    CELEBRATION = "celebration"  # Achievement/positive


class AlertType(Enum):
    """Types of alerts."""
    STREAK_BREAKING = "streak_breaking"
    BP_SPIKE = "bp_spike"
    BP_LOW = "bp_low"
    UNUSUAL_PATTERN = "unusual_pattern"
    GOAL_ACHIEVED = "goal_achieved"
    STREAK_ACHIEVED = "streak_achieved"
    TREND_WARNING = "trend_warning"
    TREND_POSITIVE = "trend_positive"


@dataclass
class Alert:
    """Represents a health alert."""
    type: AlertType
    priority: AlertPriority
    title: str
    message: str
    data: Dict[str, Any]
    created_at: datetime
    acknowledged: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary."""
        return {
            'type': self.type.value,
            'priority': self.priority.value,
            'title': self.title,
            'message': self.message,
            'data': self.data,
            'created_at': self.created_at.isoformat(),
            'acknowledged': self.acknowledged
        }


class AlertEngine:
    """Engine for detecting and generating health alerts."""

    def __init__(self):
        """Initialize the alert engine."""
        self.baselines = get_user_baselines()
        self._init_alert_table()

    def _init_alert_table(self):
        """Initialize alerts table in database."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    title TEXT NOT NULL,
                    message TEXT NOT NULL,
                    data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    acknowledged INTEGER DEFAULT 0,
                    acknowledged_at TIMESTAMP
                )
            """)
            conn.commit()

    def check_all(self, check_date: Optional[date] = None) -> List[Alert]:
        """
        Run all alert checks and return any triggered alerts.

        Args:
            check_date: Date to check (defaults to today)

        Returns:
            List of triggered alerts
        """
        if check_date is None:
            check_date = date.today()

        alerts = []

        # Run all checks
        alerts.extend(self.check_sleep_streak(check_date))
        alerts.extend(self.check_bp_anomaly(check_date))
        alerts.extend(self.check_bp_streak(check_date))
        alerts.extend(self.check_activity_streak(check_date))
        alerts.extend(self.check_trend(check_date))

        # Save alerts to database
        for alert in alerts:
            self._save_alert(alert)

        return alerts

    def check_sleep_streak(self, check_date: date) -> List[Alert]:
        """Check for consecutive nights of poor sleep."""
        alerts = []

        # Get last 7 days of data
        start_date = check_date - timedelta(days=7)
        data = get_health_data_range(start_date, check_date)

        if not data:
            return alerts

        # Check consecutive nights under 6 hours
        consecutive_poor = 0
        for day in sorted(data, key=lambda x: x['date'], reverse=True):
            sleep = day.get('sleep_hours')
            if sleep and sleep < 6:
                consecutive_poor += 1
            else:
                break

        if consecutive_poor >= 3:
            # Predict tomorrow's BP impact
            avg_bp = self.baselines.get('avg_systolic') or 140
            predicted_increase = consecutive_poor * 2  # ~2 mmHg per poor night

            alerts.append(Alert(
                type=AlertType.STREAK_BREAKING,
                priority=AlertPriority.WARNING,
                title="Poor Sleep Streak",
                message=f"⚠️ {consecutive_poor} consecutive nights under 6 hours of sleep. "
                        f"Tomorrow's BP predicted: {avg_bp + predicted_increase:.0f}-"
                        f"{avg_bp + predicted_increase + 4:.0f} mmHg. "
                        f"Prioritize 7+ hours tonight.",
                data={
                    'consecutive_nights': consecutive_poor,
                    'predicted_bp_increase': predicted_increase,
                    'recommendation': 'Prioritize 7+ hours sleep tonight'
                },
                created_at=datetime.now()
            ))

        return alerts

    def check_bp_anomaly(self, check_date: date) -> List[Alert]:
        """Check for unusual BP readings."""
        alerts = []

        # Get recent data
        start_date = check_date - timedelta(days=14)
        data = get_health_data_range(start_date, check_date)

        bp_values = [d['systolic_mean'] for d in data if d.get('systolic_mean')]

        if len(bp_values) < 3:
            return alerts

        today_data = next((d for d in data if d['date'] == check_date.isoformat()), None)
        if not today_data or not today_data.get('systolic_mean'):
            return alerts

        today_bp = today_data['systolic_mean']
        avg_bp = mean(bp_values[1:])  # Exclude today
        std_bp = stdev(bp_values[1:]) if len(bp_values) > 2 else 5

        # Check for spike (>2 standard deviations above mean)
        if today_bp > avg_bp + (2 * std_bp) and today_bp > 140:
            alerts.append(Alert(
                type=AlertType.BP_SPIKE,
                priority=AlertPriority.WARNING,
                title="Elevated BP Detected",
                message=f"🔴 Today's BP ({today_bp:.0f} mmHg) is significantly above "
                        f"your recent average ({avg_bp:.0f} mmHg). "
                        f"Check stress, sleep, and activity levels.",
                data={
                    'today_bp': today_bp,
                    'average_bp': avg_bp,
                    'deviation': (today_bp - avg_bp) / std_bp
                },
                created_at=datetime.now()
            ))

        # Check for unusually low (good!) reading
        elif today_bp < avg_bp - (2 * std_bp) and today_bp < 130:
            alerts.append(Alert(
                type=AlertType.BP_LOW,
                priority=AlertPriority.CELEBRATION,
                title="Excellent BP Reading!",
                message=f"🎉 Today's BP ({today_bp:.0f} mmHg) is exceptionally good! "
                        f"That's {avg_bp - today_bp:.0f} mmHg below your average. "
                        f"Note what you did differently!",
                data={
                    'today_bp': today_bp,
                    'average_bp': avg_bp,
                    'improvement': avg_bp - today_bp
                },
                created_at=datetime.now()
            ))

        return alerts

    def check_bp_streak(self, check_date: date) -> List[Alert]:
        """Check for consecutive days meeting BP goal."""
        alerts = []

        # Get last 14 days
        start_date = check_date - timedelta(days=14)
        data = get_health_data_range(start_date, check_date)

        if not data:
            return alerts

        goal = user_profile.bp_goal
        consecutive_under_goal = 0

        for day in sorted(data, key=lambda x: x['date'], reverse=True):
            bp = day.get('systolic_mean')
            if bp and bp < goal:
                consecutive_under_goal += 1
            else:
                break

        # Celebrate streaks at 7 and 14 days
        if consecutive_under_goal == 7:
            alerts.append(Alert(
                type=AlertType.STREAK_ACHIEVED,
                priority=AlertPriority.CELEBRATION,
                title="7-Day BP Streak!",
                message=f"🎉 7 consecutive days with BP under {goal} mmHg! "
                        f"This is your best streak in recent history. Keep it going!",
                data={
                    'streak_days': consecutive_under_goal,
                    'goal': goal
                },
                created_at=datetime.now()
            ))
        elif consecutive_under_goal == 14:
            alerts.append(Alert(
                type=AlertType.STREAK_ACHIEVED,
                priority=AlertPriority.CELEBRATION,
                title="2-Week BP Streak!",
                message=f"🏆 14 consecutive days with BP under {goal} mmHg! "
                        f"Outstanding achievement! Your habits are clearly working.",
                data={
                    'streak_days': consecutive_under_goal,
                    'goal': goal
                },
                created_at=datetime.now()
            ))

        return alerts

    def check_activity_streak(self, check_date: date) -> List[Alert]:
        """Check for activity goal streaks."""
        alerts = []

        start_date = check_date - timedelta(days=7)
        data = get_health_data_range(start_date, check_date)

        if not data:
            return alerts

        consecutive_10k = 0
        for day in sorted(data, key=lambda x: x['date'], reverse=True):
            steps = day.get('steps')
            if steps and steps >= 10000:
                consecutive_10k += 1
            else:
                break

        if consecutive_10k == 7:
            alerts.append(Alert(
                type=AlertType.GOAL_ACHIEVED,
                priority=AlertPriority.CELEBRATION,
                title="Perfect Activity Week!",
                message="🏃 7 consecutive days with 10,000+ steps! "
                        "This is excellent for your BP and overall health.",
                data={
                    'streak_days': consecutive_10k,
                    'goal': 10000
                },
                created_at=datetime.now()
            ))

        return alerts

    def check_trend(self, check_date: date) -> List[Alert]:
        """Check for concerning or positive BP trends."""
        alerts = []

        # Compare this week to last week
        this_week_start = check_date - timedelta(days=6)
        last_week_start = check_date - timedelta(days=13)
        last_week_end = check_date - timedelta(days=7)

        this_week = get_health_data_range(this_week_start, check_date)
        last_week = get_health_data_range(last_week_start, last_week_end)

        this_bp = [d['systolic_mean'] for d in this_week if d.get('systolic_mean')]
        last_bp = [d['systolic_mean'] for d in last_week if d.get('systolic_mean')]

        if len(this_bp) < 3 or len(last_bp) < 3:
            return alerts

        this_avg = mean(this_bp)
        last_avg = mean(last_bp)
        change = this_avg - last_avg

        if change >= 5:
            # Check if habits explain it
            this_sleep = mean([d['sleep_hours'] for d in this_week if d.get('sleep_hours')] or [7])
            last_sleep = mean([d['sleep_hours'] for d in last_week if d.get('sleep_hours')] or [7])

            sleep_worse = this_sleep < last_sleep - 0.5

            alerts.append(Alert(
                type=AlertType.TREND_WARNING,
                priority=AlertPriority.WARNING,
                title="BP Trending Up",
                message=f"📈 Your BP has increased by {change:.0f} mmHg this week "
                        f"(from {last_avg:.0f} to {this_avg:.0f} mmHg). "
                        f"{'Sleep quality decreased - this may be a factor.' if sleep_worse else 'Review stress and activity levels.'}",
                data={
                    'this_week_avg': this_avg,
                    'last_week_avg': last_avg,
                    'change': change,
                    'sleep_factor': sleep_worse
                },
                created_at=datetime.now()
            ))

        elif change <= -5:
            alerts.append(Alert(
                type=AlertType.TREND_POSITIVE,
                priority=AlertPriority.CELEBRATION,
                title="BP Trending Down!",
                message=f"📉 Your BP has improved by {abs(change):.0f} mmHg this week "
                        f"(from {last_avg:.0f} to {this_avg:.0f} mmHg). "
                        f"Your habits are paying off!",
                data={
                    'this_week_avg': this_avg,
                    'last_week_avg': last_avg,
                    'improvement': abs(change)
                },
                created_at=datetime.now()
            ))

        return alerts

    def check_unusual_pattern(self, check_date: date) -> List[Alert]:
        """
        Check for unusual patterns that don't fit the normal correlations.

        E.g., BP elevated despite good habits - might indicate stress,
        diet changes, or need to consult doctor.
        """
        alerts = []

        # Get last 4 days
        start_date = check_date - timedelta(days=3)
        data = get_health_data_range(start_date, check_date)

        if len(data) < 4:
            return alerts

        # Check for: good habits BUT elevated BP
        elevated_despite_good_habits = 0
        goal = user_profile.bp_goal

        for day in data:
            bp = day.get('systolic_mean')
            sleep = day.get('sleep_hours')
            steps = day.get('steps')

            if bp and sleep and steps:
                good_sleep = sleep >= 7
                good_steps = steps >= 8000
                high_bp = bp > goal + 5

                if good_sleep and good_steps and high_bp:
                    elevated_despite_good_habits += 1

        if elevated_despite_good_habits >= 3:
            alerts.append(Alert(
                type=AlertType.UNUSUAL_PATTERN,
                priority=AlertPriority.WARNING,
                title="Unusual BP Pattern",
                message=f"🔍 BP elevated for {elevated_despite_good_habits} days despite "
                        f"good sleep and activity. Possible factors: stress, dietary "
                        f"changes, medication timing. Consider consulting your doctor "
                        f"if this persists.",
                data={
                    'days_affected': elevated_despite_good_habits,
                    'possible_causes': ['stress', 'diet', 'medication timing']
                },
                created_at=datetime.now()
            ))

        return alerts

    def _save_alert(self, alert: Alert) -> int:
        """Save an alert to the database."""
        import json
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO alerts (type, priority, title, message, data, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (alert.type.value, alert.priority.value, alert.title,
                 alert.message, json.dumps(alert.data), alert.created_at)
            )
            conn.commit()
            return cursor.lastrowid

    def get_unacknowledged_alerts(self, limit: int = 10) -> List[Dict]:
        """Get unacknowledged alerts."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT * FROM alerts
                   WHERE acknowledged = 0
                   ORDER BY
                       CASE priority
                           WHEN 'critical' THEN 1
                           WHEN 'warning' THEN 2
                           WHEN 'info' THEN 3
                           WHEN 'celebration' THEN 4
                       END,
                       created_at DESC
                   LIMIT ?""",
                (limit,)
            )
            return [dict(row) for row in cursor.fetchall()]

    def acknowledge_alert(self, alert_id: int) -> bool:
        """Mark an alert as acknowledged."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """UPDATE alerts
                   SET acknowledged = 1, acknowledged_at = ?
                   WHERE id = ?""",
                (datetime.now(), alert_id)
            )
            conn.commit()
            return cursor.rowcount > 0

    def get_recent_alerts(self, days: int = 7) -> List[Dict]:
        """Get all alerts from the last N days."""
        cutoff = datetime.now() - timedelta(days=days)
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT * FROM alerts
                   WHERE created_at >= ?
                   ORDER BY created_at DESC""",
                (cutoff,)
            )
            return [dict(row) for row in cursor.fetchall()]
