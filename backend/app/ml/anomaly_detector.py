"""
ML Anomaly Detection Service
Uses Isolation Forest to detect suspicious/unusual transactions.
Trained on user's historical transaction patterns.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from typing import List, Tuple
import logging

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """
    Isolation Forest-based anomaly detector for financial transactions.
    Detects outliers based on: amount, hour of day, day of week, category encoding.
    Contamination = 0.05 (assumes ~5% of transactions are anomalous).
    """

    def __init__(self, contamination: float = 0.05):
        self.model = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=100,
        )
        self.scaler = StandardScaler()
        self.is_fitted = False
        self.min_samples = 20  # Need at least 20 transactions to train

    def _extract_features(self, transactions: List[dict]) -> np.ndarray:
        """Extract numerical features from transaction list."""
        df = pd.DataFrame(transactions)

        category_map = {
            "food": 0, "transport": 1, "entertainment": 2,
            "utilities": 3, "healthcare": 4, "shopping": 5,
            "salary": 6, "investment": 7, "other": 8
        }

        features = pd.DataFrame({
            "amount":      df["amount"].abs(),
            "hour":        pd.to_datetime(df["created_at"]).dt.hour,
            "day_of_week": pd.to_datetime(df["created_at"]).dt.dayofweek,
            "category_enc": df["category"].map(category_map).fillna(8),
            "is_expense":  (df["type"] == "expense").astype(int),
        })

        return features.values

    def fit(self, transactions: List[dict]) -> bool:
        """Train the model on historical transactions."""
        if len(transactions) < self.min_samples:
            logger.info(
                f"Not enough samples ({len(transactions)}) to train anomaly detector. "
                f"Need at least {self.min_samples}."
            )
            return False

        try:
            X = self._extract_features(transactions)
            X_scaled = self.scaler.fit_transform(X)
            self.model.fit(X_scaled)
            self.is_fitted = True
            logger.info(f"Anomaly detector trained on {len(transactions)} transactions.")
            return True
        except Exception as e:
            logger.error(f"Failed to train anomaly detector: {e}")
            return False

    def predict(self, transaction: dict) -> Tuple[bool, float]:
        """
        Predict if a transaction is anomalous.
        Returns (is_anomaly, anomaly_score).
        Score closer to -1 = more anomalous, closer to 1 = normal.
        """
        if not self.is_fitted:
            return False, 0.0

        try:
            X = self._extract_features([transaction])
            X_scaled = self.scaler.transform(X)

            prediction = self.model.predict(X_scaled)[0]    # -1 = anomaly, 1 = normal
            score = self.model.score_samples(X_scaled)[0]   # lower = more anomalous

            is_anomaly = prediction == -1
            normalized_score = abs(score)

            return is_anomaly, round(normalized_score, 4)

        except Exception as e:
            logger.error(f"Anomaly prediction failed: {e}")
            return False, 0.0

    def batch_predict(self, transactions: List[dict]) -> List[Tuple[bool, float]]:
        """Predict anomalies for a batch of transactions."""
        if not self.is_fitted:
            return [(False, 0.0)] * len(transactions)

        try:
            X = self._extract_features(transactions)
            X_scaled = self.scaler.transform(X)

            predictions = self.model.predict(X_scaled)
            scores = self.model.score_samples(X_scaled)

            return [
                (pred == -1, round(abs(score), 4))
                for pred, score in zip(predictions, scores)
            ]
        except Exception as e:
            logger.error(f"Batch anomaly prediction failed: {e}")
            return [(False, 0.0)] * len(transactions)


# Module-level singleton per user (in production: use Redis/cache)
_detectors: dict = {}


def get_detector(user_id: int) -> AnomalyDetector:
    if user_id not in _detectors:
        _detectors[user_id] = AnomalyDetector()
    return _detectors[user_id]


def retrain_detector(user_id: int, transactions: List[dict]) -> bool:
    detector = AnomalyDetector()
    success = detector.fit(transactions)
    if success:
        _detectors[user_id] = detector
    return success
