"""
Machine learning models for BP prediction.
"""
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import pickle

from config.settings import PROCESSED_DATA_DIR


class BPPredictor:
    """Blood pressure prediction using trained ML models."""

    def __init__(self, model_path: Optional[Path] = None):
        """Initialize the BP predictor."""
        self.model_path = model_path or PROCESSED_DATA_DIR / "bp_model.pkl"
        self.model = None
        self.feature_names = [
            'sleep_hours', 'sleep_efficiency_pct', 'steps',
            'vo2_max', 'stress_score', 'hrv_mean'
        ]

    def load_model(self) -> bool:
        """Load the trained model from disk."""
        if self.model_path.exists():
            with open(self.model_path, 'rb') as f:
                self.model = pickle.load(f)
            return True
        return False

    def predict(self, features: Dict[str, float]) -> Tuple[float, float]:
        """
        Predict blood pressure from features.

        Returns:
            Tuple of (predicted_bp, confidence_interval)
        """
        if self.model is None:
            if not self.load_model():
                # Return baseline estimate if no model
                return (140.0, 10.0)

        # Extract features in correct order (handle None values)
        X = [[features.get(name) or 0 for name in self.feature_names]]

        prediction = self.model.predict(X)[0]

        # Estimate confidence interval (simplified)
        confidence = 8.0  # ±8 mmHg typical

        return (prediction, confidence)

    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance from the model."""
        if self.model is None:
            self.load_model()

        if self.model is not None and hasattr(self.model, 'feature_importances_'):
            return dict(zip(self.feature_names, self.model.feature_importances_))

        # Default importance based on prior analysis
        return {
            'vo2_max': 0.30,
            'sleep_hours': 0.25,
            'steps': 0.15,
            'hrv_mean': 0.12,
            'stress_score': 0.10,
            'sleep_efficiency_pct': 0.08
        }
