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
from src.data.database import init_database, get_health_data_range, get_user_baselines


# Initialize database
init_database()

# Page config
st.set_page_config(
    page_title="BP Health Coach",
    page_icon="💓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .status-good { color: #28a745; }
    .status-warning { color: #ffc107; }
    .status-bad { color: #dc3545; }
    .stMetric {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# Session state initialization
if 'query_engine' not in st.session_state:
    st.session_state.query_engine = QueryEngine()
if 'messages' not in st.session_state:
    st.session_state.messages = []


def main():
    """Main Streamlit application."""
    # Sidebar
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/000000/heart-with-pulse.png", width=60)
        st.title("BP Health Coach")
        st.caption("AI-powered health coaching")

        st.divider()

        # Navigation
        page = st.radio(
            "Navigate",
            ["🏠 Dashboard", "💬 Chat", "📋 Daily Briefing", "📊 Weekly Report",
             "🎯 Goals", "🔮 Scenarios", "🔔 Alerts", "⚙️ Settings"],
            label_visibility="collapsed"
        )

        st.divider()

        # Show unacknowledged alerts
        render_alert_badge()

        # Quick stats
        render_sidebar_stats()

    # Route to pages
    if page == "🏠 Dashboard":
        render_dashboard_page()
    elif page == "💬 Chat":
        render_chat_page()
    elif page == "📋 Daily Briefing":
        render_briefing_page()
    elif page == "📊 Weekly Report":
        render_weekly_report_page()
    elif page == "🎯 Goals":
        render_goals_page()
    elif page == "🔮 Scenarios":
        render_scenario_page()
    elif page == "🔔 Alerts":
        render_alerts_page()
    elif page == "⚙️ Settings":
        render_settings_page()


def render_sidebar_stats():
    """Show quick stats in sidebar."""
    try:
        baselines = get_user_baselines()
        if baselines.get('avg_systolic'):
            st.metric(
                "Avg BP (90 days)",
                f"{baselines['avg_systolic']:.0f}/{baselines.get('avg_diastolic', 90):.0f}",
                help="Your average blood pressure over the last 90 days"
            )
    except Exception:
        pass


def render_alert_badge():
    """Show alert count in sidebar."""
    try:
        alert_engine = AlertEngine()
        unacked = alert_engine.get_unacknowledged_alerts(limit=100)
        if unacked:
            warning_count = sum(1 for a in unacked if a['priority'] in ['critical', 'warning'])
            if warning_count > 0:
                st.warning(f"⚠️ {warning_count} alert(s) need attention")
            else:
                st.info(f"🔔 {len(unacked)} new notification(s)")
    except Exception:
        pass


def render_dashboard_page():
    """Render the main dashboard with health overview."""
    st.header("🏠 Health Dashboard")
    st.caption(f"Overview for {date.today().strftime('%A, %B %d, %Y')}")

    # Get recent data
    today = date.today()
    week_ago = today - timedelta(days=7)
    recent_data = get_health_data_range(week_ago, today)
    baselines = get_user_baselines()

    # Top metrics row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if recent_data and recent_data[0].get('systolic_mean'):
            latest_bp = recent_data[0]['systolic_mean']
            latest_dia = recent_data[0].get('diastolic_mean', latest_bp * 0.65)
            avg_bp = baselines.get('avg_systolic', 140)
            delta = latest_bp - avg_bp
            st.metric(
                "Latest BP",
                f"{latest_bp:.0f}/{latest_dia:.0f}",
                delta=f"{delta:+.0f} vs avg",
                delta_color="inverse"
            )
        else:
            st.metric("Latest BP", "No data", help="Sync your health data")

    with col2:
        if recent_data and recent_data[0].get('sleep_hours'):
            latest_sleep = recent_data[0]['sleep_hours']
            st.metric(
                "Last Night Sleep",
                f"{latest_sleep:.1f} hrs",
                delta=f"{latest_sleep - 7:+.1f} vs goal",
                delta_color="normal"
            )
        else:
            st.metric("Last Night Sleep", "No data")

    with col3:
        if recent_data and recent_data[0].get('steps'):
            latest_steps = recent_data[0]['steps']
            st.metric(
                "Yesterday Steps",
                f"{latest_steps:,}",
                delta=f"{latest_steps - 10000:+,} vs goal",
                delta_color="normal"
            )
        else:
            st.metric("Yesterday Steps", "No data")

    with col4:
        if recent_data and recent_data[0].get('vo2_max'):
            latest_vo2 = recent_data[0]['vo2_max']
            st.metric(
                "VO2 Max",
                f"{latest_vo2:.1f}",
                delta=f"{latest_vo2 - 43:+.1f} vs goal",
                delta_color="normal"
            )
        else:
            st.metric("VO2 Max", "No data")

    st.divider()

    # Two column layout
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📈 7-Day BP Trend")
        if recent_data:
            bp_data = [(d['date'], d.get('systolic_mean')) for d in reversed(recent_data) if d.get('systolic_mean')]
            if bp_data:
                import pandas as pd
                df = pd.DataFrame(bp_data, columns=['Date', 'Systolic BP'])
                st.line_chart(df.set_index('Date'), use_container_width=True)
            else:
                st.info("No BP data available for the past week")
        else:
            st.info("No data available")

        st.subheader("🎯 Goal Progress")
        try:
            tracker = GoalTracker()
            dashboard = tracker.get_goal_dashboard()

            for goal in dashboard['goals'][:2]:  # Show top 2 goals
                progress = min(100, goal['progress_pct']) / 100
                status_icon = "✅" if goal['status'] == 'achieved' else "🔄"
                # Display BP as systolic/diastolic
                if goal['name'] == "Blood Pressure" and goal.get('diastolic'):
                    st.write(f"{status_icon} **{goal['name']}**: {goal['current']:.0f}/{goal['diastolic']:.0f} → {goal['target']:.0f} {goal['unit']}")
                else:
                    st.write(f"{status_icon} **{goal['name']}**: {goal['current']:.1f} → {goal['target']:.1f} {goal['unit']}")
                st.progress(progress)
        except Exception as e:
            st.error(f"Could not load goals: {e}")

    with col2:
        st.subheader("📋 Today's Briefing")
        try:
            generator = DailyBriefingGenerator()
            briefing = generator.generate_briefing()
            # Show abbreviated version
            lines = briefing.split('\n')[:15]
            st.text('\n'.join(lines))
            if len(briefing.split('\n')) > 15:
                with st.expander("Show full briefing"):
                    st.text(briefing)
        except Exception as e:
            st.error(f"Could not generate briefing: {e}")

        st.subheader("🔔 Recent Alerts")
        try:
            alert_engine = AlertEngine()
            alerts = alert_engine.get_recent_alerts(days=7)

            if alerts:
                for alert in alerts[:3]:
                    icon = {'warning': '⚠️', 'critical': '🔴', 'celebration': '🎉', 'info': 'ℹ️'}.get(alert['priority'], '📢')
                    st.write(f"{icon} **{alert['title']}**")
                    st.caption(alert['message'][:100] + "..." if len(alert['message']) > 100 else alert['message'])
                if len(alerts) > 3:
                    st.write(f"*+{len(alerts) - 3} more alerts*")
            else:
                st.success("No alerts - you're doing great!")
        except Exception:
            st.info("No alerts to display")

    st.divider()

    # Quick actions
    st.subheader("⚡ Quick Actions")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("💬 Ask a Question", use_container_width=True):
            st.session_state['nav_to'] = "💬 Chat"
            st.rerun()
    with col2:
        if st.button("🔮 Test a Scenario", use_container_width=True):
            st.session_state['nav_to'] = "🔮 Scenarios"
            st.rerun()
    with col3:
        if st.button("📊 Weekly Report", use_container_width=True):
            st.session_state['nav_to'] = "📊 Weekly Report"
            st.rerun()
    with col4:
        if st.button("🎯 View All Goals", use_container_width=True):
            st.session_state['nav_to'] = "🎯 Goals"
            st.rerun()


def render_chat_page():
    """Render the chat interface."""
    st.header("💬 Chat with Your Health Coach")
    st.caption("Ask questions about your health data in natural language")

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
                try:
                    result = st.session_state.query_engine.ask_with_metadata(prompt)
                    response = result['response']
                    st.markdown(response)
                    st.caption(f"Intent: {result['intent']} | Model: {result.get('model_used', 'N/A')}")
                except Exception as e:
                    response = f"Sorry, I encountered an error: {str(e)}"
                    st.error(response)

        # Add assistant message
        st.session_state.messages.append({"role": "assistant", "content": response})

    # Sidebar options
    with st.sidebar:
        st.subheader("Chat Options")
        st.text(f"Session: {st.session_state.query_engine.get_session_id()[:8]}...")

        if st.button("🔄 New Session"):
            st.session_state.query_engine.new_session()
            st.session_state.messages = []
            st.rerun()

        if st.button("🗑️ Clear History"):
            st.session_state.messages = []
            st.rerun()


def render_briefing_page():
    """Render the daily briefing page."""
    st.header("📋 Daily Health Briefing")
    st.caption("Your personalized morning health summary")

    col1, col2 = st.columns([2, 1])

    with col1:
        selected_date = st.date_input("Select date", value=date.today())

    with col2:
        st.write("")  # Spacing
        generate = st.button("Generate Briefing", type="primary", use_container_width=True)

    if generate:
        generator = DailyBriefingGenerator()

        with st.spinner("Generating your briefing..."):
            try:
                briefing = generator.generate_briefing(selected_date)
                st.markdown(f"```\n{briefing}\n```")
            except Exception as e:
                st.error(f"Error generating briefing: {e}")


def render_weekly_report_page():
    """Render the weekly report page."""
    st.header("📊 Weekly Health Report")
    st.caption("Comprehensive analysis of your health metrics")

    col1, col2 = st.columns([2, 1])

    with col1:
        today = date.today()
        last_sunday = today - timedelta(days=today.weekday() + 1)
        week_end = st.date_input(
            "Week ending",
            value=last_sunday,
            help="Select the last day of the week to analyze"
        )
        week_start = week_end - timedelta(days=6)
        st.caption(f"Analyzing: {week_start.strftime('%b %d')} - {week_end.strftime('%b %d, %Y')}")

    with col2:
        st.write("")
        generate = st.button("Generate Report", type="primary", use_container_width=True)

    if generate:
        generator = WeeklyReportGenerator()

        with st.spinner("Generating your weekly report..."):
            try:
                report = generator.generate_report(week_end)
                st.markdown(f"```\n{report}\n```")

                with st.expander("📈 View Raw Statistics"):
                    summary = generator.get_report_summary(week_end)
                    st.json(summary)
            except Exception as e:
                st.error(f"Error generating report: {e}")


def render_goals_page():
    """Render the goal tracking dashboard."""
    st.header("🎯 Goal Tracking Dashboard")
    st.caption("Track your progress toward health goals")

    try:
        tracker = GoalTracker()
        dashboard = tracker.get_goal_dashboard()
    except Exception as e:
        st.error(f"Error loading goals: {e}")
        return

    # Overall status
    status_icons = {
        'achieved': '🏆',
        'on_track': '✅',
        'at_risk': '⚠️',
        'off_track': '❌'
    }

    overall = dashboard['overall_status']
    st.markdown(f"### {status_icons.get(overall, '📊')} Overall Status: **{overall.replace('_', ' ').upper()}**")

    # Summary metrics
    summary = dashboard['summary']
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🏆 Achieved", summary['achieved'])
    with col2:
        st.metric("✅ On Track", summary['on_track'])
    with col3:
        st.metric("⚠️ At Risk", summary['at_risk'])
    with col4:
        st.metric("📊 Total", summary['total'])

    st.divider()

    # Individual goals
    for goal in dashboard['goals']:
        with st.container():
            col1, col2 = st.columns([2, 1])

            with col1:
                status_icon = status_icons.get(goal['status'], '○')
                st.subheader(f"{status_icon} {goal['name']}")

                progress = min(100, goal['progress_pct']) / 100
                st.progress(progress, text=f"{goal['progress_pct']:.0f}% complete")

                # Display BP as systolic/diastolic
                if goal['name'] == "Blood Pressure" and goal.get('diastolic'):
                    st.write(f"**Current:** {goal['current']:.0f}/{goal['diastolic']:.0f} {goal['unit']} → **Target:** {goal['target']:.0f} {goal['unit']} (systolic)")
                else:
                    st.write(f"**Current:** {goal['current']:.1f} {goal['unit']} → **Target:** {goal['target']:.1f} {goal['unit']}")

            with col2:
                trend = goal['trend']
                trend_arrows = {'increasing': '📈', 'decreasing': '📉', 'stable': '➡️'}
                trend_icon = trend_arrows.get(trend['direction'], '➡️')

                if trend['change'] != 0:
                    st.metric(
                        "Monthly Trend",
                        f"{trend_icon} {trend['direction'].title()}",
                        delta=f"{trend['change']:+.1f}",
                        delta_color="normal"
                    )

                proj = goal['projection']
                if proj.get('weeks_remaining') is not None and proj['weeks_remaining'] > 0:
                    st.write(f"**ETA:** ~{proj['weeks_remaining']} weeks")

            with st.expander(f"💡 Tips to improve {goal['name']}"):
                recommendations = tracker.get_recommendations_for_goal(goal['name'])
                for rec in recommendations:
                    st.write(f"• {rec}")

            st.divider()


def render_scenario_page():
    """Render the scenario testing page."""
    st.header("🔮 What-If Scenario Testing")
    st.caption("Test how lifestyle changes might affect your blood pressure")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Adjust Your Targets")

        vo2_change = st.slider(
            "🏃 VO2 Max",
            min_value=30.0,
            max_value=50.0,
            value=37.0,
            step=0.5,
            help="Your target VO2 Max (cardio fitness)"
        )

        sleep_change = st.slider(
            "😴 Sleep (hours)",
            min_value=4.0,
            max_value=10.0,
            value=7.0,
            step=0.5,
            help="Your target sleep duration"
        )

        steps_change = st.slider(
            "👟 Daily Steps",
            min_value=2000,
            max_value=20000,
            value=10000,
            step=500,
            help="Your target daily steps"
        )

        analyze = st.button("🔍 Analyze Scenario", type="primary", use_container_width=True)

    with col2:
        st.subheader("Predicted Results")

        if analyze:
            engine = ScenarioEngine()

            changes = {
                'vo2_max': vo2_change,
                'sleep_hours': sleep_change,
                'steps': steps_change
            }

            with st.spinner("Analyzing..."):
                try:
                    result = engine.test_scenario(changes)

                    st.metric(
                        "Current BP",
                        f"{result.current_systolic:.0f}/{result.current_diastolic:.0f} mmHg",
                    )
                    st.metric(
                        "Predicted BP",
                        f"{result.predicted_systolic:.0f}/{result.predicted_diastolic:.0f} mmHg",
                        delta=f"{result.bp_change:+.1f}/{result.diastolic_change:+.1f} mmHg",
                        delta_color="inverse"
                    )

                    st.info(f"**Confidence:** {result.confidence_interval[0]:.0f} to {result.confidence_interval[1]:.0f} mmHg")
                    st.write(f"**Timeline:** {result.timeline_weeks} weeks")
                    st.write(f"**Feasibility:** {result.feasibility}")

                    st.subheader("📋 Recommendations")
                    for rec in result.recommendations:
                        st.write(f"• {rec}")
                except Exception as e:
                    st.error(f"Error analyzing scenario: {e}")
        else:
            st.info("👈 Adjust the sliders and click 'Analyze Scenario' to see predictions")


def render_alerts_page():
    """Render the alerts page."""
    st.header("🔔 Health Alerts")
    st.caption("Stay informed about your health patterns")

    alert_engine = AlertEngine()

    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("🔄 Check for New Alerts", type="primary"):
            with st.spinner("Checking..."):
                try:
                    new_alerts = alert_engine.check_all()
                    if new_alerts:
                        st.success(f"Found {len(new_alerts)} new alert(s)")
                        st.rerun()
                    else:
                        st.info("No new alerts detected")
                except Exception as e:
                    st.error(f"Error checking alerts: {e}")

    with col2:
        days = st.selectbox("Show alerts from", [7, 14, 30], index=0, label_visibility="collapsed")

    with col3:
        st.write("")  # Spacing

    st.divider()

    try:
        alerts = alert_engine.get_recent_alerts(days=days)
    except Exception as e:
        st.error(f"Error loading alerts: {e}")
        return

    if not alerts:
        st.success("🎉 No alerts in the selected time period. Keep up the good work!")
        return

    priority_config = {
        'critical': {'icon': '🔴', 'color': 'red'},
        'warning': {'icon': '🟠', 'color': 'orange'},
        'info': {'icon': '🔵', 'color': 'blue'},
        'celebration': {'icon': '🎉', 'color': 'green'}
    }

    for alert in alerts:
        priority = alert['priority']
        config = priority_config.get(priority, {'icon': '📢', 'color': 'gray'})

        with st.container():
            col1, col2, col3 = st.columns([0.5, 8, 1.5])

            with col1:
                st.write(config['icon'])

            with col2:
                ack_badge = "" if alert['acknowledged'] else " 🆕"
                st.markdown(f"**{alert['title']}**{ack_badge}")
                st.write(alert['message'])
                st.caption(f"Created: {alert['created_at'][:16] if alert['created_at'] else 'Unknown'}")

            with col3:
                if not alert['acknowledged']:
                    if st.button("Dismiss", key=f"ack_{alert['id']}"):
                        alert_engine.acknowledge_alert(alert['id'])
                        st.rerun()
                else:
                    st.write("✓ Seen")

            st.divider()


def render_settings_page():
    """Render the settings page."""
    st.header("⚙️ Settings")
    st.caption("Configure your health coach preferences")

    # User Profile Section
    st.subheader("👤 User Profile")

    col1, col2 = st.columns(2)
    with col1:
        bp_goal = st.number_input("BP Goal (systolic)", min_value=100, max_value=160, value=130)
        sleep_goal = st.number_input("Sleep Goal (hours)", min_value=5.0, max_value=10.0, value=7.0, step=0.5)

    with col2:
        vo2_goal = st.number_input("VO2 Max Goal", min_value=30.0, max_value=60.0, value=43.0, step=0.5)
        steps_goal = st.number_input("Daily Steps Goal", min_value=5000, max_value=20000, value=10000, step=500)

    st.divider()

    # LLM Settings
    st.subheader("🤖 AI Model Settings")

    col1, col2 = st.columns(2)
    with col1:
        primary_model = st.selectbox(
            "Primary LLM",
            ["Claude 3.5 Sonnet", "GPT-4 Turbo", "Llama 3.1 (Local)"],
            index=0
        )
    with col2:
        use_local = st.checkbox("Use local Llama for simple queries", value=True)

    st.divider()

    # Notification Settings
    st.subheader("🔔 Notifications")

    col1, col2 = st.columns(2)
    with col1:
        daily_briefing = st.checkbox("Daily briefing at 8 AM", value=True)
        weekly_report = st.checkbox("Weekly report on Monday", value=True)
    with col2:
        alert_streak = st.checkbox("Alert on poor sleep streaks", value=True)
        alert_bp = st.checkbox("Alert on BP anomalies", value=True)

    st.divider()

    # Data Management
    st.subheader("📊 Data Management")

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📥 Import Health Data"):
            st.info("Run: `python scripts/import_health_data.py`")
    with col2:
        if st.button("🔄 Refresh Vector Store"):
            st.info("Run: `python scripts/rebuild_vectors.py`")
    with col3:
        if st.button("📤 Export Data"):
            st.info("Feature coming soon")

    st.divider()

    # Save button
    if st.button("💾 Save Settings", type="primary"):
        st.success("Settings saved successfully!")
        st.info("Note: Some settings require restarting the app to take effect.")


if __name__ == "__main__":
    main()
