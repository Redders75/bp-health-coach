"""
Weekly report generation feature.

Generates comprehensive weekly health summaries every Monday,
analyzing trends, patterns, and providing actionable recommendations.
"""
from datetime import date, timedelta
from typing import Dict, Any, Optional, List
from statistics import mean, stdev

from src.data.database import get_health_data_range, get_user_baselines
from src.models.ml_models import BPPredictor
from src.llm.claude import ClaudeClient
from config.settings import user_profile


class WeeklyReportGenerator:
    """Generate comprehensive weekly health reports."""

    def __init__(self):
        """Initialize the report generator."""
        self.predictor = BPPredictor()
        self.claude = ClaudeClient()

    def generate_report(self, week_end_date: Optional[date] = None) -> str:
        """
        Generate a weekly health report.

        Args:
            week_end_date: Last day of the week to report on (defaults to yesterday)

        Returns:
            Formatted report string
        """
        if week_end_date is None:
            week_end_date = date.today() - timedelta(days=1)

        week_start = week_end_date - timedelta(days=6)

        # Get this week's data
        week_data = get_health_data_range(week_start, week_end_date)

        # Get previous week for comparison
        prev_week_start = week_start - timedelta(days=7)
        prev_week_end = week_start - timedelta(days=1)
        prev_week_data = get_health_data_range(prev_week_start, prev_week_end)

        # Get baselines
        baselines = get_user_baselines()

        # Calculate weekly stats
        week_stats = self._calculate_week_stats(week_data)
        prev_stats = self._calculate_week_stats(prev_week_data)

        # Analyze patterns
        patterns = self._analyze_patterns(week_data)

        # Generate the report
        report = self._compose_report(
            week_start,
            week_end_date,
            week_data,
            week_stats,
            prev_stats,
            baselines,
            patterns
        )

        return report

    def _calculate_week_stats(self, data: List[Dict]) -> Dict[str, Any]:
        """Calculate statistics for a week of data."""
        if not data:
            return {}

        stats = {}

        # BP stats
        systolic_values = [d['systolic_mean'] for d in data if d.get('systolic_mean')]
        diastolic_values = [d['diastolic_mean'] for d in data if d.get('diastolic_mean')]
        if systolic_values:
            stats['bp_avg'] = mean(systolic_values)
            stats['bp_min'] = min(systolic_values)
            stats['bp_max'] = max(systolic_values)
            stats['bp_std'] = stdev(systolic_values) if len(systolic_values) > 1 else 0
            stats['bp_days'] = len(systolic_values)
        if diastolic_values:
            stats['diastolic_avg'] = mean(diastolic_values)

        # Sleep stats
        sleep_values = [d['sleep_hours'] for d in data if d.get('sleep_hours')]
        if sleep_values:
            stats['sleep_avg'] = mean(sleep_values)
            stats['sleep_min'] = min(sleep_values)
            stats['sleep_max'] = max(sleep_values)
            stats['sleep_days_under_7'] = sum(1 for s in sleep_values if s < 7)

        # Steps stats
        steps_values = [d['steps'] for d in data if d.get('steps')]
        if steps_values:
            stats['steps_avg'] = mean(steps_values)
            stats['steps_total'] = sum(steps_values)
            stats['steps_days_over_10k'] = sum(1 for s in steps_values if s >= 10000)

        # VO2 Max
        vo2_values = [d['vo2_max'] for d in data if d.get('vo2_max')]
        if vo2_values:
            stats['vo2_avg'] = mean(vo2_values)
            stats['vo2_latest'] = vo2_values[0]  # Most recent

        stats['total_days'] = len(data)

        return stats

    def _analyze_patterns(self, data: List[Dict]) -> Dict[str, Any]:
        """Analyze patterns in the week's data."""
        patterns = {
            'best_day': None,
            'worst_day': None,
            'trends': [],
            'correlations': []
        }

        if not data:
            return patterns

        # Find best/worst BP days
        bp_days = [(d['date'], d['systolic_mean'], d) for d in data if d.get('systolic_mean')]
        if bp_days:
            bp_days_sorted = sorted(bp_days, key=lambda x: x[1])
            patterns['best_day'] = {
                'date': bp_days_sorted[0][0],
                'bp': bp_days_sorted[0][1],
                'data': bp_days_sorted[0][2]
            }
            patterns['worst_day'] = {
                'date': bp_days_sorted[-1][0],
                'bp': bp_days_sorted[-1][1],
                'data': bp_days_sorted[-1][2]
            }

        # Identify trends
        if len(bp_days) >= 3:
            first_half = mean([d[1] for d in bp_days[len(bp_days)//2:]])
            second_half = mean([d[1] for d in bp_days[:len(bp_days)//2]])
            if second_half < first_half - 2:
                patterns['trends'].append('improving')
            elif second_half > first_half + 2:
                patterns['trends'].append('worsening')
            else:
                patterns['trends'].append('stable')

        # Analyze what made best/worst days different
        if patterns['best_day'] and patterns['worst_day']:
            best = patterns['best_day']['data']
            worst = patterns['worst_day']['data']

            if best.get('sleep_hours') and worst.get('sleep_hours'):
                sleep_diff = best['sleep_hours'] - worst['sleep_hours']
                if abs(sleep_diff) > 1:
                    patterns['correlations'].append({
                        'factor': 'sleep',
                        'observation': f"Best day had {sleep_diff:+.1f}hrs more sleep"
                    })

            if best.get('steps') and worst.get('steps'):
                steps_diff = best['steps'] - worst['steps']
                if abs(steps_diff) > 2000:
                    patterns['correlations'].append({
                        'factor': 'steps',
                        'observation': f"Best day had {steps_diff:+,} more steps"
                    })

        return patterns

    def _compose_report(
        self,
        week_start: date,
        week_end: date,
        week_data: List[Dict],
        stats: Dict,
        prev_stats: Dict,
        baselines: Dict,
        patterns: Dict
    ) -> str:
        """Compose the full weekly report."""
        start_str = week_start.strftime("%B %d")
        end_str = week_end.strftime("%B %d, %Y")

        if not stats:
            return f"""WEEKLY HEALTH REPORT: {start_str} - {end_str}

No health data available for this week.
Please ensure your Apple Health data is synced.
"""

        report = f"""WEEKLY HEALTH REPORT: {start_str} - {end_str}

{'='*60}

1. BLOOD PRESSURE SUMMARY
{'='*60}
"""

        # BP Section
        if stats.get('bp_avg'):
            diastolic_avg = stats.get('diastolic_avg', stats['bp_avg'] * 0.65)
            report += f"""
Average: {stats['bp_avg']:.0f}/{diastolic_avg:.0f} mmHg
Range: {stats['bp_min']:.0f} - {stats['bp_max']:.0f} mmHg (systolic)
Variability: ±{stats['bp_std']:.1f} mmHg
Days with readings: {stats['bp_days']}/7
"""
            # Compare to previous week
            if prev_stats.get('bp_avg'):
                change = stats['bp_avg'] - prev_stats['bp_avg']
                arrow = "↓" if change < 0 else "↑" if change > 0 else "→"
                report += f"vs Previous Week: {change:+.1f} mmHg {arrow}\n"

            # Compare to goal
            goal = user_profile.bp_goal
            if stats['bp_avg'] < goal:
                report += f"Status: BELOW your {goal} mmHg goal! Excellent!\n"
            else:
                gap = stats['bp_avg'] - goal
                report += f"Status: {gap:.0f} mmHg above your {goal} mmHg goal\n"

        # Sleep Section
        report += f"""
{'='*60}

2. SLEEP ANALYSIS
{'='*60}
"""
        if stats.get('sleep_avg'):
            report += f"""
Average: {stats['sleep_avg']:.1f} hours/night
Range: {stats['sleep_min']:.1f} - {stats['sleep_max']:.1f} hours
Days under 7 hours: {stats['sleep_days_under_7']}/7
"""
            if prev_stats.get('sleep_avg'):
                change = stats['sleep_avg'] - prev_stats['sleep_avg']
                arrow = "↑" if change > 0 else "↓" if change < 0 else "→"
                report += f"vs Previous Week: {change:+.1f} hours {arrow}\n"
        else:
            report += "\nNo sleep data recorded this week.\n"

        # Activity Section
        report += f"""
{'='*60}

3. ACTIVITY SUMMARY
{'='*60}
"""
        if stats.get('steps_avg'):
            report += f"""
Daily Average: {stats['steps_avg']:,.0f} steps
Weekly Total: {stats['steps_total']:,} steps
Days over 10,000: {stats['steps_days_over_10k']}/7
"""
            if prev_stats.get('steps_avg'):
                change = stats['steps_avg'] - prev_stats['steps_avg']
                pct = (change / prev_stats['steps_avg']) * 100 if prev_stats['steps_avg'] else 0
                arrow = "↑" if change > 0 else "↓" if change < 0 else "→"
                report += f"vs Previous Week: {change:+,.0f} steps ({pct:+.0f}%) {arrow}\n"
        else:
            report += "\nNo step data recorded this week.\n"

        # VO2 Max Section
        if stats.get('vo2_avg'):
            report += f"""
{'='*60}

4. FITNESS (VO2 MAX)
{'='*60}

Current: {stats['vo2_latest']:.1f} mL/kg/min
Week Average: {stats['vo2_avg']:.1f} mL/kg/min
Goal: {user_profile.vo2_max_goal} mL/kg/min
"""
            gap = user_profile.vo2_max_goal - stats['vo2_latest']
            if gap > 0:
                report += f"Gap to goal: {gap:.1f} mL/kg/min\n"
            else:
                report += "Status: GOAL ACHIEVED!\n"

        # Patterns & Insights
        report += f"""
{'='*60}

5. KEY INSIGHTS
{'='*60}
"""
        if patterns.get('best_day'):
            best = patterns['best_day']
            report += f"""
BEST DAY: {best['date']}
- BP: {best['bp']:.0f} mmHg
- Sleep: {best['data'].get('sleep_hours', 'N/A')} hours
- Steps: {best['data'].get('steps', 'N/A'):,}
"""

        if patterns.get('worst_day'):
            worst = patterns['worst_day']
            report += f"""
CHALLENGING DAY: {worst['date']}
- BP: {worst['bp']:.0f} mmHg
- Sleep: {worst['data'].get('sleep_hours', 'N/A')} hours
- Steps: {worst['data'].get('steps', 'N/A'):,}
"""

        if patterns.get('correlations'):
            report += "\nPATTERNS OBSERVED:\n"
            for corr in patterns['correlations']:
                report += f"- {corr['observation']}\n"

        if patterns.get('trends'):
            trend = patterns['trends'][0]
            if trend == 'improving':
                report += "\nTREND: BP improving through the week! Keep it up.\n"
            elif trend == 'worsening':
                report += "\nTREND: BP increased through the week. Review stress/sleep patterns.\n"
            else:
                report += "\nTREND: BP stable throughout the week.\n"

        # Recommendations
        report += f"""
{'='*60}

6. ACTION PLAN FOR NEXT WEEK
{'='*60}
"""
        recommendations = self._generate_weekly_recommendations(stats, patterns, baselines)
        for i, rec in enumerate(recommendations, 1):
            report += f"\n{i}. {rec['action']}\n"
            report += f"   Why: {rec['reason']}\n"
            report += f"   Target: {rec['target']}\n"

        # Prediction for next week
        report += f"""
{'='*60}

7. NEXT WEEK FORECAST
{'='*60}
"""
        if stats.get('bp_avg'):
            # Simple projection based on trends
            if patterns.get('trends') and patterns['trends'][0] == 'improving':
                projected = stats['bp_avg'] - 2
            elif patterns.get('trends') and patterns['trends'][0] == 'worsening':
                projected = stats['bp_avg'] + 2
            else:
                projected = stats['bp_avg']

            report += f"""
If current habits continue:
- Expected BP: {projected:.0f} mmHg (±5)
- Confidence: Moderate (based on recent patterns)
"""

        report += f"""
{'='*60}
Report generated: {date.today().strftime('%Y-%m-%d')}
{'='*60}
"""

        return report

    def _generate_weekly_recommendations(
        self,
        stats: Dict,
        patterns: Dict,
        baselines: Dict
    ) -> List[Dict[str, str]]:
        """Generate actionable recommendations for the coming week."""
        recommendations = []

        # Sleep recommendation
        if stats.get('sleep_days_under_7', 0) >= 3:
            recommendations.append({
                'action': 'Prioritize Sleep',
                'reason': f"You had {stats['sleep_days_under_7']} days under 7 hours this week",
                'target': '7+ hours every night'
            })

        # Steps recommendation
        if stats.get('steps_days_over_10k', 0) < 4:
            recommendations.append({
                'action': 'Increase Daily Activity',
                'reason': f"Only {stats['steps_days_over_10k']} days hit 10k steps",
                'target': 'Hit 10,000 steps at least 5 days'
            })

        # BP-specific recommendation
        if stats.get('bp_avg', 0) > user_profile.bp_goal:
            gap = stats['bp_avg'] - user_profile.bp_goal
            recommendations.append({
                'action': 'Focus on BP Reduction',
                'reason': f"Average BP is {gap:.0f} mmHg above goal",
                'target': f"Reduce average BP by {min(gap, 5):.0f} mmHg"
            })

        # VO2 recommendation
        if stats.get('vo2_latest', 50) < user_profile.vo2_max_goal:
            recommendations.append({
                'action': 'Add Cardio Sessions',
                'reason': 'VO2 Max is your strongest BP predictor',
                'target': '3-4 cardio sessions of 30+ minutes'
            })

        # Best day replication
        if patterns.get('best_day') and patterns.get('correlations'):
            recommendations.append({
                'action': 'Replicate Your Best Day',
                'reason': f"Your best BP ({patterns['best_day']['bp']:.0f} mmHg) shows what works",
                'target': 'Follow the same sleep/activity pattern 4+ days'
            })

        return recommendations[:5]  # Limit to 5 recommendations

    def get_report_summary(self, week_end_date: Optional[date] = None) -> Dict[str, Any]:
        """
        Get a structured summary of the weekly report.

        Useful for APIs and dashboards.
        """
        if week_end_date is None:
            week_end_date = date.today() - timedelta(days=1)

        week_start = week_end_date - timedelta(days=6)
        week_data = get_health_data_range(week_start, week_end_date)
        stats = self._calculate_week_stats(week_data)
        patterns = self._analyze_patterns(week_data)

        return {
            'week_start': week_start.isoformat(),
            'week_end': week_end_date.isoformat(),
            'stats': stats,
            'patterns': patterns,
            'days_with_data': len(week_data)
        }
