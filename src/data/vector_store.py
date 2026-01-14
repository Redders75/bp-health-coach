"""
ChromaDB vector store for semantic search of health data.
"""
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
from datetime import date

from config.settings import CHROMA_DB_DIR, vector_store_config


class HealthVectorStore:
    """Vector store for health data embeddings and semantic search."""

    def __init__(self):
        """Initialize ChromaDB client and collection."""
        self.client = chromadb.PersistentClient(
            path=str(CHROMA_DB_DIR),
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_or_create_collection(
            name=vector_store_config.collection_name,
            metadata={"description": "Daily health summaries for semantic search"}
        )

    def create_daily_summary(self, target_date: date, data: Dict[str, Any]) -> str:
        """Convert structured health data to natural language summary."""
        bp = data.get('systolic_mean', 'N/A')
        sleep_hrs = data.get('sleep_hours', 0)
        sleep_eff = data.get('sleep_efficiency_pct', 0)
        steps = data.get('steps', 0)
        vo2 = data.get('vo2_max', 'N/A')
        stress = data.get('stress_score', 'N/A')

        # Determine BP category
        if isinstance(bp, (int, float)):
            if bp < 120:
                bp_cat = "normal"
            elif bp < 130:
                bp_cat = "elevated"
            elif bp < 140:
                bp_cat = "stage 1 hypertension"
            else:
                bp_cat = "stage 2 hypertension"
        else:
            bp_cat = "unknown"

        # Determine sleep quality
        if sleep_hrs >= 7:
            sleep_quality = "good"
        elif sleep_hrs >= 6:
            sleep_quality = "fair"
        else:
            sleep_quality = "poor"

        summary = (
            f"{target_date.isoformat()}: "
            f"BP {bp} mmHg ({bp_cat}). "
            f"Sleep {sleep_hrs:.1f}hrs ({sleep_eff:.0f}% efficiency) - {sleep_quality}. "
            f"Activity {steps:,} steps. "
            f"VO2 Max {vo2}. "
            f"Stress score {stress}."
        )

        return summary

    def add_daily_summary(self, target_date: date, data: Dict[str, Any]) -> None:
        """Add a daily health summary to the vector store."""
        summary = self.create_daily_summary(target_date, data)
        doc_id = f"day_{target_date.isoformat()}"

        # Upsert to handle updates
        self.collection.upsert(
            documents=[summary],
            ids=[doc_id],
            metadatas=[{
                "date": target_date.isoformat(),
                "systolic": data.get('systolic_mean'),
                "sleep_hours": data.get('sleep_hours'),
                "steps": data.get('steps')
            }]
        )

    def search_similar_days(
        self,
        query: str,
        n_results: int = None
    ) -> List[Dict[str, Any]]:
        """Search for days similar to the query."""
        if n_results is None:
            n_results = vector_store_config.n_results

        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )

        # Format results
        similar_days = []
        if results['documents'] and results['documents'][0]:
            for i, doc in enumerate(results['documents'][0]):
                similar_days.append({
                    'summary': doc,
                    'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                    'distance': results['distances'][0][i] if results['distances'] else None
                })

        return similar_days

    def search_by_pattern(self, pattern: str, n_results: int = 10) -> List[Dict[str, Any]]:
        """Search for days matching a specific pattern description."""
        return self.search_similar_days(pattern, n_results)

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store collection."""
        return {
            "name": self.collection.name,
            "count": self.collection.count()
        }


# Singleton instance
_vector_store: Optional[HealthVectorStore] = None


def get_vector_store() -> HealthVectorStore:
    """Get or create the singleton vector store instance."""
    global _vector_store
    if _vector_store is None:
        _vector_store = HealthVectorStore()
    return _vector_store
