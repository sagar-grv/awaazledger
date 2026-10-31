"""Tests for TrustService user reputation scoring."""

from app.services.trust_service import TrustService


def test_high_trust_user():
    service = TrustService()
    profile = service.get_user_trust(user_id=1)  # Rohit Verma (score 95)
    assert profile["trust_score"] == 95
    assert profile["risk_band"] == "LOW"
    assert profile["blacklisted"] is False
    assert profile["velocity_flag"] is False


def test_blacklisted_user():
    service = TrustService()
    profile = service.get_user_trust(user_id=3)  # Vikram Singh (score 25, blacklisted)
    assert profile["trust_score"] == 25
    assert profile["risk_band"] in ["CRITICAL", "HIGH"]
    assert profile["blacklisted"] is True
    assert profile["velocity_flag"] is True  # previous_dispute_count = 5 >= 3
