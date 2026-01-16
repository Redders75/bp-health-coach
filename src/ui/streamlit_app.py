"""
Streamlit web interface for the BP Health Coach.
"""
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
from datetime import date

from src.features.query_answering import QueryEngine
from src.features.daily_briefing import DailyBriefingGenerator
from src.features.scenario_testing import ScenarioEngine
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
        ["Chat", "Daily Briefing", "Scenario Testing"]
    )

    if page == "Chat":
        render_chat_page()
    elif page == "Daily Briefing":
        render_briefing_page()
    else:
        render_scenario_page()


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

        st.markdown(briefing)


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


if __name__ == "__main__":
    main()
