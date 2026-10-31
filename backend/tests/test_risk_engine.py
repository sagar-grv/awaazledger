"""Tests for deterministic risk engine scoring and classification."""

import pytest
from app.agent.risk_engine import RiskEngine


@pytest.fixture
def risk_engine():
    return RiskEngine()


def test_low_risk_scenario(risk_engine):
    reconciliation = {
        "invalid_utr": False,
        "user_mismatch": False,
        "duplicate_debit": False,
        "ghost_success": False,
        "amount_mismatch": False,
        "cbs_amount": 450.0,
        "claimed_amount": 450.0,
        "risk_signals": {
            "blacklisted": False,
            "velocity_flag": False,
            "trust_score": 95,
            "low_trust": False,
        },
        "policy_inputs": {
            "rbi_tat_breach_candidate": False,
        },
    }
    result = risk_engine.evaluate(reconciliation)
    assert result["risk_level"] == "LOW"
    assert result["fraud_score"] == 0.0
    assert result["risk_score"] == 0.0
    assert any("User trust score is high" in r for r in result["reasons"])


def test_invalid_utr_scenario(risk_engine):
    reconciliation = {
        "invalid_utr": True,
        "user_mismatch": False,
        "duplicate_debit": False,
        "ghost_success": False,
        "amount_mismatch": False,
        "risk_signals": {
            "blacklisted": False,
            "velocity_flag": False,
            "trust_score": 90,
            "low_trust": False,
        },
        "policy_inputs": {},
    }
    result = risk_engine.evaluate(reconciliation)
    assert result["risk_level"] == "CRITICAL"
    assert result["fraud_score"] >= 50.0
    assert result["signals"]["invalid_utr"] is True
    assert any("Invalid or untraceable UTR" in r for r in result["reasons"])


def test_duplicate_debit_scenario(risk_engine):
    reconciliation = {
        "invalid_utr": False,
        "user_mismatch": False,
        "duplicate_debit": True,
        "ghost_success": False,
        "amount_mismatch": False,
        "risk_signals": {
            "blacklisted": False,
            "velocity_flag": False,
            "trust_score": 90,
            "low_trust": False,
        },
        "policy_inputs": {},
    }
    result = risk_engine.evaluate(reconciliation)
    assert result["risk_level"] == "HIGH"
    assert result["risk_score"] >= 20.0
    assert result["signals"]["duplicate_debit"] is True
    assert any("Duplicate payment debit detected" in r for r in result["reasons"])


def test_blacklisted_user_scenario(risk_engine):
    reconciliation = {
        "invalid_utr": False,
        "user_mismatch": False,
        "duplicate_debit": False,
        "ghost_success": False,
        "amount_mismatch": False,
        "risk_signals": {
            "blacklisted": True,
            "velocity_flag": False,
            "trust_score": 20,
            "low_trust": True,
        },
        "policy_inputs": {},
    }
    result = risk_engine.evaluate(reconciliation)
    assert result["risk_level"] == "CRITICAL"
    assert result["fraud_score"] >= 80.0
    assert result["signals"]["blacklisted"] is True
