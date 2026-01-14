#!/usr/bin/env python3
"""
Script to initialize the database and vector store.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data.database import init_database
from src.data.vector_store import get_vector_store
from config.settings import SQLITE_DB_PATH, CHROMA_DB_DIR


def main():
    """Initialize all data stores."""
    print("Setting up BP Health Coach database...")

    # Ensure directories exist
    SQLITE_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    CHROMA_DB_DIR.mkdir(parents=True, exist_ok=True)

    # Initialize SQLite
    print(f"Initializing SQLite database at {SQLITE_DB_PATH}")
    init_database()
    print("SQLite database initialized.")

    # Initialize ChromaDB
    print(f"Initializing ChromaDB at {CHROMA_DB_DIR}")
    vector_store = get_vector_store()
    stats = vector_store.get_collection_stats()
    print(f"ChromaDB initialized. Collection '{stats['name']}' has {stats['count']} documents.")

    print("\nDatabase setup complete!")


if __name__ == "__main__":
    main()
