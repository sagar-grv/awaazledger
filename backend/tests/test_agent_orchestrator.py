"""Tests for AgentOrchestrator running the complete autonomous lifecycle across dispute scenarios."""

import pytest
from app.agent.state_machine import AgentOrchestrator
from app.models.dispute import Dispute
from app.schemas.dispute import DisputeStatus, AgentDecision, ActionType


def test_orchestrator_scn_01_auto_resolve(db_session):
    orchestrator = AgentOrchestrator(db_session)
    dispute = db_session.query(Dispute).filter(Dispute.dispute_code == "DISP-SCN-01").first()
    assert dispute is not None

    result = orchestrator.run_for_dispute(dispute.id)

    assert result["dispute_id"] == dispute.id
    assert result["decision"] == AgentDecision.AUTO_RESOLVE.value
    assert result["status"] == DisputeStatus.AUTO_CREDITED.value
    assert result["resolved"] is True
    assert result["risk_level"] == "LOW"

    action_types = [a["action_type"] for a in result["actions_executed"]]
    assert ActionType.BRIDGE_CREDIT.value in action_types
    assert ActionType.NPCI_DISPUTE_RAISED.value in action_types

    assert len(result["explanation_user"]) > 0
    assert len(result["explanation_internal"]) > 0
    assert len(result["state_history"]) >= 8


def test_orchestrator_scn_03_high_value_escalation(db_session):
    orchestrator = AgentOrchestrator(db_session)
    dispute = db_session.query(Dispute).filter(Dispute.dispute_code == "DISP-SCN-03").first()
    assert dispute is not None

    result = orchestrator.run_for_dispute(dispute.id)

    assert result["decision"] == AgentDecision.HUMAN_ESCALATE.value
    assert result["status"] == DisputeStatus.ESCALATED.value
    assert result["resolved"] is False

    action_types = [a["action_type"] for a in result["actions_executed"]]
    assert ActionType.ESCALATE_HUMAN.value in action_types
    assert ActionType.BRIDGE_CREDIT.value not in action_types


def test_orchestrator_scn_05_fraud_blocked(db_session):
    orchestrator = AgentOrchestrator(db_session)
    dispute = db_session.query(Dispute).filter(Dispute.dispute_code == "DISP-SCN-05").first()
    assert dispute is not None

    result = orchestrator.run_for_dispute(dispute.id)

    assert result["decision"] == AgentDecision.FRAUD_BLOCK.value
    assert result["status"] == DisputeStatus.FRAUD_BLOCKED.value
    assert result["risk_level"] == "CRITICAL"
    assert result["fraud_score"] >= 50.0

    action_types = [a["action_type"] for a in result["actions_executed"]]
    assert ActionType.FRAUD_ALERT.value in action_types


def test_orchestrator_ghost_success(db_session):
    orchestrator = AgentOrchestrator(db_session)
    dispute = db_session.query(Dispute).filter(Dispute.dispute_code == "DISP-SCN-EDGE-01").first()
    assert dispute is not None

    result = orchestrator.run_for_dispute(dispute.id)

    assert result["decision"] == AgentDecision.AUTO_RESOLVE.value
    assert result["status"] == DisputeStatus.RECEIPT_GENERATED.value
    assert result["resolved"] is True

    action_types = [a["action_type"] for a in result["actions_executed"]]
    assert ActionType.GENERATE_RECEIPT.value in action_types
    assert ActionType.BRIDGE_CREDIT.value not in action_types


def test_orchestrator_duplicate_debit(db_session):
    orchestrator = AgentOrchestrator(db_session)
    dispute = db_session.query(Dispute).filter(Dispute.dispute_code == "DISP-SCN-EDGE-02").first()
    assert dispute is not None

    result = orchestrator.run_for_dispute(dispute.id)

    assert result["decision"] == AgentDecision.HUMAN_ESCALATE.value
    assert result["status"] == DisputeStatus.ESCALATED.value

    action_types = [a["action_type"] for a in result["actions_executed"]]
    assert ActionType.ESCALATE_HUMAN.value in action_types
