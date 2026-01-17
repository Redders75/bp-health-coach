"""
Streamlit web interface for the BP Health Coach.
"""
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
from datetime import date, timedelta

from src.features.query_answering import QueryEngine
from src.features.daily_briefing import DailyBriefingGenerator
from src.features.scenario_testing import ScenarioEngine
from src.features.weekly_report import WeeklyReportGenerator
from src.features.alerts import AlertEngine
from src.features.goal_tracking import GoalTracker
from src.data.database import init_database


# Initialize database
init_database()

# Page config
st.set_page_config(
    page_title="BP Health Coach",
    page_icon="💓",
    layout="wide"
)

# Session state initialization
if 'query_engine' not in st.session_state:
    st.session_state.query_engine = QueryEngine()
if 'messages' not in st.session_state:
    st.session_state.messages = []


def main():
    """Main Streamlit application."""
    st.title("💓 BP Health Coach")
    st.caption("AI-powered blood pressure health coaching")

    # Sidebar navigation
    page = st.sidebar.selectbox(
        "Navigation",
        ["Chat", "Daily Briefing", "Weekly Report", "Goals", "Scenario Testing", "Alerts"]
    )

    # Show unacknowledged alerts count in sidebar
    render_alert_badge()

    if page == "Chat":
        render_chat_page()
    elif page == "Daily Briefing":
        render_briefing_page()
    elif page == "Weekly Report":
        render_weekly_report_page()
    elif page == "Goals":
        render_goals_page()
    elif page == "Scenario Testing":
        render_scenario_page()
    elif page == "Alerts":
        render_alerts_page()


def render_alert_badge():
    """Show alert count in sidebar."""
    try:
        alert_engine = AlertEngine()
        unacked = alert_engine.get_unacknowledged_alerts(limit=100)
        if unacked:
            warning_count = sum(1 for a in unacked if a['priority'] in ['critical', 'warning'])
            if warning_count > 0:
                st.sidebar.warning(f"⚠️ {warning_count} alert(s) need attention")
            else:
                st.sidebar.info(f"🔔 {len(unacked)} new notification(s)")
    except Exception:
        pass  # Silently fail if alerts table doesn't exist yet


def render_chat_page():
    """Render the chat interface."""
    st.header("Chat with Your Health Coach")

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("Ask about your health..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                result = st.session_state.query_engine.ask_with_metadata(prompt)
                response = result['response']
            st.markdown(response)
            st.caption(f"Intent: {result['intent']} | Model: {result.get('model_used', 'N/A')}")

        # Add assistant message
        st.session_state.messages.append({"role": "assistant", "content": response})

    # Sidebar options
    with st.sidebar:
        st.subheader("Session Info")
        st.text(f"Session ID: {st.session_state.query_engine.get_session_id()[:8]}...")

        if st.button("New Session"):
            st.session_state.query_engine.new_session()
            st.session_state.messages = []
            st.rerun()


def render_briefing_page():
    """Render the daily briefing page."""
    st.header("Daily Health Briefing")

    # Date selector
    selected_date = st.date_input("Select date", value=date.today())

    if st.button("Generate Briefing"):
        generator = DailyBriefingGenerator()

        with st.spinner("Generating your briefing..."):
            briefing = generator.generate_briefing(selected_date)

        st.markdown(f"```\n{briefing}\n```")


def render_weekly_report_page():
    """Render the weekly report page."""
    st.header("Weekly Health Report")

    st.write("Comprehensive analysis of your health metrics for the week.")

    # Week selector
    col1, col2 = st.columns(2)
    with col1:
        # Default to last complete week
        today = date.today()
        last_sunday = today - timedelta(days=today.weekday() + 1)
        week_end = st.date_input(
            "Week ending",
            value=last_sunday,
            help="Select the last day of the week you want to analyze"
        )

    with col2:
        week_start = week_end - timedelta(days=6)
        st.write(f"**Week:** {week_start.strftime('%b %d')} - {week_end.strftime('%b %d, %Y')}")

    if st.button("Generate Report", type="primary"):
        generator = WeeklyReportGenerator()

        with st.spinner("Generating your weekly report..."):
            report = generator.generate_report(week_end)

        # Display in a code block for formatting
        st.markdown(f"```\n{report}\n```")

        # Also show summary stats
        with st.expander("View Raw Statistics"):
            summary = generator.get_report_summary(week_end)
            st.json(summary)


def render_goals_page():
    """Render the goal tracking dashboard."""
    st.header("Goal Tracking Dashboard")

    tracker = GoalTracker()
    dashboard = tracker.get_goal_dashboard()

    # Overall status banner
    status_colors = {
        'achieved': 'green',
        'on_track': 'blue',
        'at_risk': 'orange',
        'off_track': 'red'
    }
    status_icons = {
        'achieved': '🏆',
        'on_track': '✅',
        'at_risk': '⚠️',
        'off_track': '❌'
    }

    overall = dashboard['overall_status']
    st.markdown(
        f"### {status_icons.get(overall, '📊')} Overall Status: **{overall.upper()}**"
    )

    summary = dashboard['summary']
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Achieved", summary['achieved'])
    with col2:
        st.metric("On Track", summary['on_track'])
    with col3:
        st.metric("At Risk", summary['at_risk'])
    with col4:
        st.metric("Total Goals", summary['total'])

    st.divider()

    # Individual goals
    for goal in dashboard['goals']:
        with st.container():
            col1, col2 = st.columns([2, 1])

            with col1:
                status_icon = status_icons.get(goal['status'], '○')
                st.subheader(f"{status_icon} {goal['name']}")

                # Progress bar
                progress = min(100, goal['progress_pct']) / 100
                st.progress(progress, text=f"{goal['progress_pct']:.0f}% complete")

                # Current vs target
                st.write(
                    f"**Current:** {goal['current']:.1f} {goal['unit']} → "
                    f"**Target:** {goal['target']:.1f} {goal['unit']}"
                )

            with col2:
                # Trend indicator
                trend = goal['trend']
                trend_arrows = {'increasing': '↑', 'decreasing': '↓', 'stable': '→'}
                trend_arrow = trend_arrows.get(trend['direction'], '→')

                if trend['change'] != 0:
                    st.metric(
                        "Monthly Trend",
                        f"{trend_arrow} {trend['direction'].title()}",
                        delta=f"{trend['change']:+.1f}",
                        delta_color="normal"
                    )
                else:
                    st.write(f"**Trend:** {trend_arrow} Stable")

                # Projection
                proj = goal['projection']
                if proj.get('weeks_remaining') is not None:
                    if proj['weeks_remaining'] > 0:
                        st.write(f"**ETA:** ~{proj['weeks_remaining']} weeks")
                    else:
                        st.write("**Status:** Goal reached!")

            # Recommendations expander
            with st.expander(f"Tips to improve {goal['name']}"):
                recommendations = tracker.get_recommendations_for_goal(goal['name'])
                for rec in recommendations:
                    st.write(f"• {rec}")

            st.divider()


def render_scenario_page():
    """Render the scenario testing page."""
    st.header("What-If Scenario Testing")

    st.write("Test how changes to your health metrics might affect your blood pressure.")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Proposed Changes")

        vo2_change = st.slider(
            "VO2 Max",
            min_value=30.0,
            max_value=50.0,
            value=37.0,
            step=0.5,
            help="Your target VO2 Max"
        )

        sleep_change = st.slider(
            "Sleep (hours)",
            min_value=4.0,
            max_value=10.0,
            value=7.0,
            step=0.5,
            help="Your target sleep hours"
        )

        steps_change = st.slider(
            "Daily Steps",
            min_value=2000,
            max_value=20000,
            value=10000,
            step=500,
            help="Your target daily steps"
        )

    with col2:
        st.subheader("Analysis")

        if st.button("Analyze Scenario", type="primary"):
            engine = ScenarioEngine()

            changes = {
                'vo2_max': vo2_change,
                'sleep_hours': sleep_change,
                'steps': steps_change
            }

            with st.spinner("Analyzing..."):
                result = engine.test_scenario(changes)

            # Display results - use inverse delta_color so decreases show as green (good for BP)
            st.metric(
                "Current BP",
                f"{result.current_systolic:.0f}/{result.current_diastolic:.0f} mmHg",
            )
            st.metric(
                "Predicted BP",
                f"{result.predicted_systolic:.0f}/{result.predicted_diastolic:.0f} mmHg",
                delta=f"{result.bp_change:+.1f}/{result.diastolic_change:+.1f} mmHg",
                delta_color="inverse"  # Negative (decrease) = green, Positive (increase) = red
            )

            st.write(f"**Confidence Interval:** {result.confidence_interval[0]:.0f} to {result.confidence_interval[1]:.0f} mmHg (systolic)")
            st.write(f"**Timeline:** {result.timeline_weeks} weeks")
            st.write(f"**Feasibility:** {result.feasibility}")

            st.subheader("Recommendations")
            for rec in result.recommendations:
                st.write(f"• {rec}")


def render_alerts_page():
    """Render the alerts page."""
    st.header("Health Alerts")

    alert_engine = AlertEngine()

    # Action buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Check for New Alerts", type="primary"):
            with st.spinner("Checking..."):
                new_alerts = alert_engine.check_all()
            if new_alerts:
                st.success(f"Found {len(new_alerts)} new alert(s)")
                st.rerun()
            else:
                st.info("No new alerts detected")

    with col2:
        days = st.selectbox("Show alerts from", [7, 14, 30], index=0)

    st.divider()

    # Get alerts
    alerts = alert_engine.get_recent_alerts(days=days)

    if not alerts:
        st.info("No alerts in the selected time period.")
        return

    # Priority icons and colors
    priority_config = {
        'critical': {'icon': '🔴', 'color': 'red'},
        'warning': {'icon': '🟠', 'color': 'orange'},
        'info': {'icon': '🔵', 'color': 'blue'},
        'celebration': {'icon': '🎉', 'color': 'green'}
    }

    # Display alerts
    for alert in alerts:
        priority = alert['priority']
        config = priority_config.get(priority, {'icon': '📢', 'color': 'gray'})

        with st.container():
            col1, col2, col3 = st.columns([0.5, 8, 1.5])

            with col1:
                st.write(config['icon'])

            with col2:
                # Title and acknowledged status
                ack_badge = "" if alert['acknowledged'] else " 🆕"
                st.markdown(f"**{alert['title']}**{ack_badge}")
                st.write(alert['message'])
                st.caption(f"Created: {alert['created_at']}")

            with col3:
                if not alert['acknowledged']:
                    if st.button("Dismiss", key=f"ack_{alert['id']}"):
                        alert_engine.acknowledge_alert(alert['id'])
                        st.rerun()
                else:
                    st.write("✓ Seen")

            st.divider()

    # Summary stats
    with st.sidebar:
        st.subheader("Alert Summary")
        total = len(alerts)
        unacked = sum(1 for a in alerts if not a['acknowledged'])
        st.write(f"Total: {total}")
        st.write(f"Unread: {unacked}")

        # Breakdown by type
        by_priority = {}
        for alert in alerts:
            p = alert['priority']
            by_priority[p] = by_priority.get(p, 0) + 1

        for priority, count in by_priority.items():
            config = priority_config.get(priority, {'icon': '📢'})
            st.write(f"{config['icon']} {priority.title()}: {count}")


if __name__ == "__main__":
    main()
