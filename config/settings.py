"""
Configuration settings for BP Health Coach.
"""
import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv

# Base paths
PROJECT_ROOT = Path(__file__).parent.parent

# Load environment variables from .env file
load_dotenv(PROJECT_ROOT / ".env")
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
CHROMA_DB_DIR = DATA_DIR / "chroma_db"

# Database settings
SQLITE_DB_PATH = PROCESSED_DATA_DIR / "health_data.db"

# LLM API Keys (loaded from environment)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# LLM Model configurations
@dataclass
class LLMConfig:
    """Configuration for LLM models."""
    claude_model: str = "claude-sonnet-4-20250514"
    gpt4_model: str = "gpt-4-turbo"
    llama_model: str = "llama-3.1-70b"

    # Cost thresholds
    max_tokens_per_query: int = 4096
    max_cost_per_day: float = 2.0

# Vector store settings
@dataclass
class VectorStoreConfig:
    """Configuration for ChromaDB vector store."""
    collection_name: str = "health_summaries"
    embedding_model: str = "all-MiniLM-L6-v2"
    n_results: int = 5

# User profile defaults
@dataclass
class UserProfile:
    """User health profile and goals."""
    name: str = "Andy"
    bp_goal: int = 130
    sleep_goal: float = 7.0
    steps_goal: int = 10000
    vo2_max_goal: float = 43.0

# Application settings
@dataclass
class AppConfig:
    """General application configuration."""
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    response_timeout: int = 30  # seconds
    briefing_time: str = "08:00"  # Daily briefing time

# Create default instances
llm_config = LLMConfig()
vector_store_config = VectorStoreConfig()
user_profile = UserProfile()
app_config = AppConfig()
