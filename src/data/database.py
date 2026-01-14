"""
SQLite database operations for health data.
"""
import sqlite3
from datetime import date, datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

from config.settings import SQLITE_DB_PATH


@contextmanager
def get_connection():
    """Context manager for database connections."""
    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_database():
    """Initialize the database with required tables."""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Daily health data table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_health_data (
                date DATE PRIMARY KEY,
                systolic_mean REAL,
                diastolic_mean REAL,
                heart_rate_mean REAL,
                steps INTEGER,
                sleep_hours REAL,
                sleep_efficiency_pct REAL,
                vo2_max REAL,
                stress_score REAL,
                hrv_mean REAL,
                respiratory_rate REAL,
                active_calories REAL,
                exercise_minutes INTEGER,
                standing_hours INTEGER,
                awakenings INTEGER,
                deep_sleep_pct REAL,
                rem_sleep_pct REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Conversations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_query TEXT NOT NULL,
                assistant_response TEXT NOT NULL,
                llm_model TEXT,
                tokens_used INTEGER,
                cost_usd REAL,
                intent_type TEXT,
                confidence REAL
            )
        """)

        # Create index on session_id for faster lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_conversations_session
            ON conversations(session_id)
        """)

        conn.commit()


def get_health_data_for_date(target_date: date) -> Optional[Dict[str, Any]]:
    """Retrieve health data for a specific date."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM daily_health_data WHERE date = ?",
            (target_date.isoformat(),)
        )
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None


def get_health_data_range(start_date: date, end_date: date) -> List[Dict[str, Any]]:
    """Retrieve health data for a date range."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT * FROM daily_health_data
               WHERE date BETWEEN ? AND ?
               ORDER BY date DESC""",
            (start_date.isoformat(), end_date.isoformat())
        )
        return [dict(row) for row in cursor.fetchall()]


def save_conversation(
    session_id: str,
    user_query: str,
    assistant_response: str,
    llm_model: str = None,
    tokens_used: int = None,
    cost_usd: float = None,
    intent_type: str = None,
    confidence: float = None
) -> int:
    """Save a conversation turn to the database."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO conversations
               (session_id, user_query, assistant_response, llm_model,
                tokens_used, cost_usd, intent_type, confidence)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (session_id, user_query, assistant_response, llm_model,
             tokens_used, cost_usd, intent_type, confidence)
        )
        conn.commit()
        return cursor.lastrowid


def get_recent_conversations(session_id: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Retrieve recent conversations for a session."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT * FROM conversations
               WHERE session_id = ?
               ORDER BY timestamp DESC
               LIMIT ?""",
            (session_id, limit)
        )
        return [dict(row) for row in cursor.fetchall()]


def get_user_baselines() -> Dict[str, float]:
    """Calculate user's baseline health metrics from historical data."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                AVG(systolic_mean) as avg_systolic,
                AVG(diastolic_mean) as avg_diastolic,
                AVG(sleep_hours) as avg_sleep,
                AVG(steps) as avg_steps,
                AVG(vo2_max) as avg_vo2_max,
                AVG(hrv_mean) as avg_hrv
            FROM daily_health_data
            WHERE date >= date('now', '-90 days')
        """)
        row = cursor.fetchone()
        if row:
            return dict(row)
        return {}
