"""Tests for ActionDispatcher handling financial execution, idempotency, and audit trails."""

import pytest
from app.agent.action_dispatcher import ActionDispatcher
from app.models.dispute import Dispute
from app.models.bridge_credit import BridgeCredit
from app.models.escalation import Escalation
from app.schemas.dispute import ActionType, AgentDecision


def test_action_dispatcher_bridge_credit_idempotency(db_session):
    dispatcher = ActionDispatcher(db_session)
    dispute = db_session.query(Dispute).filter(Dispute.dispute_code == "DISP-SCN-01").first()
    assert dispute is not None

    decision = {
        "decision": AgentDecision.AUTO_RESOLVE,
        "actions": [ActionType.BRIDGE_CREDIT],
        "rule_matched": "RBI_TAT_BRIDGE_CREDIT_LOW_RISK",
    }
    reconciliation = {"cbs_amount": 450.0}
    risk = {"risk_level": "LOW", "fraud_score": 0.0}

    # First run
    results1 = dispatcher.execute(dispute, decision, reconciliation, risk)
    assert len(results1) == 1
    assert results1[0]["status"] == "SUCCESS"
    assert results1[0]["action_type"] == ActionType.BRIDGE_CREDIT.value

    # Verify bridge credit row exists
    bc = db_session.query(BridgeCredit).filter(BridgeCredit.dispute_id == dispute.id).first()
    assert bc is not None
    assert bc.amount == 450.0

    # Second run (Idempotency test)
    results2 = dispatcher.execute(dispute, decision, reconciliation, risk)
    assert len(results2) == 1
    assert results2[0]["status"] == "ALREADY_ISSUED"
    assert "credit_id" in results2[0]["payload"]


def test_action_dispatcher_escalation(db_session):
    dispatcher = ActionDispatcher(db_session)
    dispute = db_session.query(Dispute).filter(Dispute.dispute_code == "DISP-SCN-03").first()
    assert dispute is not None

    decision = {
        "decision": AgentDecision.HUMAN_ESCALATE,
        "actions": [ActionType.ESCALATE_HUMAN],
        "rule_matched": "HUMAN_IN_LOOP_ESCALATION",
        "reasons": ["Amount INR 18500 exceeds autonomous ceiling"],
    }
    reconciliation = {"cbs_amount": 18500.0}
    risk = {"risk_level": "LOW", "fraud_score": 0.0}

    results = dispatcher.execute(dispute, decision, reconciliation, risk)
    assert len(results) == 1
    assert results[0]["action_type"] == ActionType.ESCALATE_HUMAN.value

    esc = db_session.query(Escalation).filter(Escalation.dispute_id == dispute.id).first()
    assert esc is not None
    assert esc.assigned_to == "SUPERVISOR"
    assert esc.priority == "HIGH"


def test_action_dispatcher_generate_receipt(db_session):
    dispatcher = ActionDispatcher(db_session)
    dispute = db_session.query(Dispute).filter(Dispute.dispute_code == "DISP-SCN-EDGE-01").first()
    assert dispute is not None

    decision = {
        "decision": AgentDecision.AUTO_RESOLVE,
        "actions": [ActionType.GENERATE_RECEIPT],
        "rule_matched": "GHOST_SUCCESS_VERIFIED_RECEIPT",
    }
    reconciliation = {"beneficiary_credited": True, "cbs_amount": 780.0}
    risk = {"risk_level": "LOW"}

    results = dispatcher.execute(dispute, decision, reconciliation, risk)
    assert len(results) == 1
    assert results[0]["action_type"] == ActionType.GENERATE_RECEIPT.value
    assert "receipt_id" in results[0]["payload"]
