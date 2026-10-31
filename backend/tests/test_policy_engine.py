"""Tests for deterministic policy engine governing money movement and routing."""

import pytest
from app.agent.policy_engine import PolicyEngine
from app.schemas.dispute import AgentDecision, ActionType


@pytest.fixture
def policy_engine():
    return PolicyEngine(auto_credit_ceiling=2000.0, min_trust_score=85)


def test_scn_01_bridge_credit(policy_engine):
    reconciliation = {
        "cbs_debited": True,
        "beneficiary_credited": False,
        "invalid_utr": False,
        "user_mismatch": False,
        "duplicate_debit": False,
        "ghost_success": False,
        "risk_signals": {"trust_score": 95},
        "policy_inputs": {"eligible_for_automatic_bridge_credit_signal": True},
    }
    risk = {"risk_level": "LOW", "fraud_score": 0.0, "reasons": []}
    dispute = {"amount": 450.0}

    decision = policy_engine.decide(reconciliation, risk, dispute)
    assert decision["decision"] == AgentDecision.AUTO_RESOLVE
    assert decision["rule_matched"] == "RBI_TAT_BRIDGE_CREDIT_LOW_RISK"
    assert decision["eligible_for_bridge_credit"] is True
    assert ActionType.BRIDGE_CREDIT in decision["actions"]
    assert ActionType.NPCI_DISPUTE_RAISED in decision["actions"]
    assert ActionType.START_RBI_TAT_TIMER in decision["actions"]


def test_scn_01_with_rbi_compensation_action(policy_engine):
    reconciliation = {
        "cbs_debited": True,
        "beneficiary_credited": False,
        "invalid_utr": False,
        "user_mismatch": False,
        "duplicate_debit": False,
        "ghost_success": False,
        "risk_signals": {"trust_score": 95},
        "policy_inputs": {
            "eligible_for_automatic_bridge_credit_signal": True,
            "rbi_compensation_signal": True,
        },
    }
    risk = {"risk_level": "LOW", "fraud_score": 0.0, "reasons": []}
    dispute = {"amount": 500.0}

    decision = policy_engine.decide(reconciliation, risk, dispute)
    assert ActionType.RBI_PENALTY_CLAIM in decision["actions"]


def test_scn_03_high_value_escalation(policy_engine):
    reconciliation = {
        "cbs_debited": True,
        "beneficiary_credited": False,
        "risk_signals": {"trust_score": 98},
        "policy_inputs": {"requires_human_review_signal": True},
    }
    risk = {"risk_level": "LOW", "fraud_score": 0.0, "reasons": []}
    dispute = {"amount": 14500.0}

    decision = policy_engine.decide(reconciliation, risk, dispute)
    assert decision["decision"] == AgentDecision.HUMAN_ESCALATE
    assert decision["rule_matched"] == "HUMAN_IN_LOOP_ESCALATION"
    assert decision["requires_human_review"] is True
    assert ActionType.ESCALATE_HUMAN in decision["actions"]


def test_scn_05_fraud_control_block(policy_engine):
    reconciliation = {
        "invalid_utr": True,
        "risk_signals": {"blacklisted": True, "trust_score": 15},
        "policy_inputs": {"fraud_block_signal": True},
    }
    risk = {"risk_level": "CRITICAL", "fraud_score": 85.0, "reasons": ["Invalid UTR"]}
    dispute = {"amount": 800.0}

    decision = policy_engine.decide(reconciliation, risk, dispute)
    assert decision["decision"] == AgentDecision.FRAUD_BLOCK
    assert decision["rule_matched"] == "FRAUD_CONTROL_BLOCK"
    assert decision["fraud_block"] is True
    assert ActionType.FRAUD_ALERT in decision["actions"]


def test_ghost_success_verified_receipt(policy_engine):
    reconciliation = {
        "cbs_debited": True,
        "beneficiary_credited": True,
        "ghost_success": True,
        "risk_signals": {"trust_score": 92},
        "policy_inputs": {},
    }
    risk = {"risk_level": "LOW", "fraud_score": 0.0, "reasons": []}
    dispute = {"amount": 250.0}

    decision = policy_engine.decide(reconciliation, risk, dispute)
    assert decision["decision"] == AgentDecision.AUTO_RESOLVE
    assert decision["rule_matched"] == "GHOST_SUCCESS_VERIFIED_RECEIPT"
    assert ActionType.GENERATE_RECEIPT in decision["actions"]
    assert decision["eligible_for_bridge_credit"] is False


def test_duplicate_debit_escalates(policy_engine):
    reconciliation = {
        "cbs_debited": True,
        "duplicate_debit": True,
        "risk_signals": {"trust_score": 90},
        "policy_inputs": {"requires_human_review_signal": True},
    }
    risk = {"risk_level": "HIGH", "fraud_score": 10.0, "reasons": ["Duplicate debit"]}
    dispute = {"amount": 300.0}

    decision = policy_engine.decide(reconciliation, risk, dispute)
    assert decision["decision"] == AgentDecision.HUMAN_ESCALATE
    assert decision["requires_human_review"] is True
