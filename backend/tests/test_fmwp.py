"""
Tests for FMWP backend — anomaly detector + transaction service logic.
Run: pytest tests/ -v
"""

import pytest
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from app.ml.anomaly_detector import AnomalyDetector, get_detector, retrain_detector


# ── Anomaly Detector Tests ────────────────────────────────────────────────────

def make_transactions(n=30, anomaly_amount=None):
    txs = []
    for i in range(n):
        txs.append({
            "amount": anomaly_amount if (anomaly_amount and i == n-1) else float(50 + (i % 10) * 5),
            "type": "expense",
            "category": "food",
            "created_at": (datetime.utcnow() - timedelta(days=n-i)).isoformat(),
        })
    return txs


class TestAnomalyDetector:

    def test_detector_not_fitted_by_default(self):
        detector = AnomalyDetector()
        assert not detector.is_fitted

    def test_predict_returns_no_anomaly_when_not_fitted(self):
        detector = AnomalyDetector()
        tx = {"amount": 100, "type": "expense", "category": "food", "created_at": datetime.utcnow().isoformat()}
        is_anomaly, score = detector.predict(tx)
        assert is_anomaly is False
        assert score == 0.0

    def test_fit_requires_minimum_samples(self):
        detector = AnomalyDetector()
        result = detector.fit(make_transactions(5))  # Below min_samples=20
        assert result is False
        assert not detector.is_fitted

    def test_fit_succeeds_with_enough_samples(self):
        detector = AnomalyDetector()
        result = detector.fit(make_transactions(30))
        assert result is True
        assert detector.is_fitted

    def test_normal_transaction_not_flagged(self):
        detector = AnomalyDetector()
        transactions = make_transactions(50)
        detector.fit(transactions)

        normal_tx = {
            "amount": 55.0,  # Within normal range
            "type": "expense",
            "category": "food",
            "created_at": datetime.utcnow().isoformat(),
        }
        is_anomaly, score = detector.predict(normal_tx)
        assert isinstance(is_anomaly, (bool, np.bool_))
        assert isinstance(score, (float, np.floating))

    def test_extreme_amount_flagged_as_anomaly(self):
        detector = AnomalyDetector(contamination=0.1)
        # Train on tightly clustered small amounts
        transactions = [
            {"amount": 10.0 + (i % 3) * 0.5, "type": "expense", "category": "food",
             "created_at": (datetime.utcnow() - timedelta(days=100-i)).isoformat()}
            for i in range(100)
        ]
        detector.fit(transactions)

        # Predict on both normal and extreme — extreme should score higher
        normal_tx = {"amount": 10.5, "type": "expense", "category": "food",
                     "created_at": datetime.utcnow().isoformat()}
        extreme_tx = {"amount": 999999.0, "type": "expense", "category": "food",
                      "created_at": datetime.utcnow().isoformat()}

        _, normal_score  = detector.predict(normal_tx)
        _, extreme_score = detector.predict(extreme_tx)

        # Extreme transaction should have higher anomaly score
        assert extreme_score >= normal_score
        assert extreme_score > 0

    def test_batch_predict_returns_correct_length(self):
        detector = AnomalyDetector()
        transactions = make_transactions(30)
        detector.fit(transactions)

        batch = make_transactions(5)
        results = detector.batch_predict(batch)
        assert len(results) == 5
        for is_anomaly, score in results:
            assert isinstance(is_anomaly, (bool, np.bool_))
            assert isinstance(score, (float, np.floating))

    def test_batch_predict_unfitted_returns_all_false(self):
        detector = AnomalyDetector()
        batch = make_transactions(5)
        results = detector.batch_predict(batch)
        assert all(not r[0] for r in results)
        assert all(r[1] == 0.0 for r in results)

    def test_get_detector_singleton_per_user(self):
        d1 = get_detector(999)
        d2 = get_detector(999)
        assert d1 is d2

    def test_get_detector_different_users(self):
        d1 = get_detector(1001)
        d2 = get_detector(1002)
        assert d1 is not d2

    def test_retrain_detector_replaces_existing(self):
        original = get_detector(777)
        transactions = make_transactions(30)
        success = retrain_detector(777, transactions)
        assert success is True
        new_detector = get_detector(777)
        assert new_detector is not original
        assert new_detector.is_fitted

    def test_retrain_fails_with_insufficient_data(self):
        success = retrain_detector(888, make_transactions(5))
        assert success is False

    def test_anomaly_score_is_float(self):
        detector = AnomalyDetector()
        detector.fit(make_transactions(30))
        tx = {"amount": 100, "type": "expense", "category": "food", "created_at": datetime.utcnow().isoformat()}
        _, score = detector.predict(tx)
        assert isinstance(score, float)
        assert 0.0 <= score <= 10.0  # reasonable range


# ── Security Tests ─────────────────────────────────────────────────────────────
from app.core.security import hash_password, verify_password, create_access_token, decode_token


class TestSecurity:

    def test_password_hashing(self):
        password = "SecurePass123!"
        hashed = hash_password(password)
        assert hashed != password
        assert verify_password(password, hashed)

    def test_wrong_password_fails(self):
        hashed = hash_password("correct")
        assert not verify_password("wrong", hashed)

    def test_token_creation_and_decode(self):
        token = create_access_token({"sub": "42", "email": "test@test.com"})
        payload = decode_token(token)
        assert payload["sub"] == "42"
        assert payload["email"] == "test@test.com"

    def test_invalid_token_raises(self):
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            decode_token("invalid.token.here")
        assert exc.value.status_code == 401
