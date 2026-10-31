"""Tests for the supervisor escalation service."""

import pytest
from datetime import datetime, timezone, timedelta
from app.models.dispute import Dispute
from app.models.escalation import Escalation
from app.models.user import User
from app.models.bridge_credit import BridgeCredit
from app.models.action import Action
from app.models.audit_log import AuditLog
from app.services.escalation_service import EscalationService


def test_list_escalations_and_sla(db_session):
    service = EscalationService(db_session)

    # Fetch existing dispute
    dispute = db_session.query(Dispute).filter(Dispute.dispute_code == "DISP-SCN-03").first()
    assert dispute is not None

    now = datetime.now(timezone.utc)
    # Create escalation with SLA
    esc = Escalation(
        dispute_id=dispute.id,
        reason="Amount exceeds threshold",
        priority="HIGH",
        assigned_to="SUPERVISOR",
        sla_deadline=now + timedelta(hours=4),
        status="OPEN",
        created_at=now,
    )
    db_session.add(esc)
    db_session.commit()

    listing = service.list_escalations()
    assert listing.total >= 1
    assert listing.open_count >= 1

    item = next(i for i in listing.items if i.id == esc.id)
    assert item.priority == "HIGH"
    assert item.dispute_code == "DISP-SCN-03"
    assert item.is_sla_breached is False
    assert item.hours_to_sla is not None


def test_escalation_detail_dossier(db_session):
    service = EscalationService(db_session)
    dispute = db_session.query(Dispute).filter(Dispute.dispute_code == "DISP-SCN-03").first()
    esc = db_session.query(Escalation).filter(Escalation.dispute_id == dispute.id).first()
    if not esc:
        esc = Escalation(
            dispute_id=dispute.id,
            reason="High value transaction",
            priority="HIGH",
            status="OPEN",
        )
        db_session.add(esc)
        db_session.commit()

    detail = service.get_escalation_detail(esc.id)
    assert detail.escalation.id == esc.id
    assert detail.dispute["dispute_code"] == "DISP-SCN-03"
    assert detail.user["phone"] is not None
    assert detail.risk_assessment is not None
    assert detail.policy_evaluation is not None


def test_approve_escalation_and_bridge_credit(db_session):
    service = EscalationService(db_session)
    dispute = db_session.query(Dispute).filter(Dispute.dispute_code == "DISP-SCN-03").first()
    esc = db_session.query(Escalation).filter(Escalation.dispute_id == dispute.id).first()
    if not esc:
        esc = Escalation(
            dispute_id=dispute.id,
            reason="High value transaction",
            priority="HIGH",
            status="OPEN",
        )
        db_session.add(esc)
        db_session.commit()

    res = service.approve_escalation(
        escalation_id=esc.id,
        note="Approved after checking salary slips and merchant record",
        supervisor_id="SUP_MEERA",
    )
    assert res.action == "APPROVE"
    assert res.status == "APPROVED"
    assert res.bridge_credit_id is not None

    # Check database side effects
    db_session.refresh(esc)
    assert esc.status == "APPROVED"
    assert "Approved after checking" in esc.resolution_note

    db_session.refresh(dispute)
    assert dispute.status == "RESOLVED"
    assert dispute.agent_decision == "MANUALLY_APPROVED"

    bc = db_session.query(BridgeCredit).filter(BridgeCredit.id == res.bridge_credit_id).first()
    assert bc is not None
    assert bc.status == "ISSUED"
    assert bc.amount == (dispute.claimed_amount or dispute.amount)

    # Check idempotent second approval
    res2 = service.approve_escalation(escalation_id=esc.id, note="Second click")
    assert res2.status == "ALREADY_APPROVED"
    assert res2.bridge_credit_id == bc.id


def test_reject_escalation(db_session):
    service = EscalationService(db_session)
    dispute = db_session.query(Dispute).filter(Dispute.dispute_code == "DISP-SCN-04").first()
    esc = Escalation(
        dispute_id=dispute.id,
        reason="Duplicate complaint suspicion",
        priority="MEDIUM",
        status="OPEN",
    )
    db_session.add(esc)
    db_session.commit()

    res = service.reject_escalation(
        escalation_id=esc.id,
        reason="User verified merchant already settled in cash",
        supervisor_id="SUP_ANAND",
    )
    assert res.action == "REJECT"
    assert res.status == "REJECTED"

    db_session.refresh(esc)
    assert esc.status == "REJECTED"
    db_session.refresh(dispute)
    assert dispute.status == "REJECTED"


def test_request_info_escalation(db_session):
    service = EscalationService(db_session)
    dispute = db_session.query(Dispute).filter(Dispute.dispute_code == "DISP-SCN-02").first()
    esc = Escalation(
        dispute_id=dispute.id,
        reason="Need merchant passbook scan",
        priority="LOW",
        status="OPEN",
    )
    db_session.add(esc)
    db_session.commit()

    res = service.request_info(
        escalation_id=esc.id,
        prompt="Please share bank statement showing debit on 28-Oct",
        supervisor_id="SUP_MEERA",
    )
    assert res.action == "REQUEST_INFO"
    assert res.status == "INFO_REQUESTED"

    db_session.refresh(esc)
    assert esc.status == "INFO_REQUESTED"
    db_session.refresh(dispute)
    assert dispute.status == "INFO_REQUESTED"


def test_mark_fraud_escalation(db_session):
    service = EscalationService(db_session)
    dispute = db_session.query(Dispute).filter(Dispute.dispute_code == "DISP-SCN-05").first()
    esc = Escalation(
        dispute_id=dispute.id,
        reason="Synthetic UTR detected",
        priority="CRITICAL",
        status="OPEN",
    )
    db_session.add(esc)
    db_session.commit()

    res = service.mark_fraud(
        escalation_id=esc.id,
        reason="Confirmed fake UTR attempt across 3 accounts",
        supervisor_id="SUP_LEAD",
    )
    assert res.action == "MARK_FRAUD"
    assert res.status == "FRAUD_CONFIRMED"

    db_session.refresh(esc)
    assert esc.status == "FRAUD_CONFIRMED"
    db_session.refresh(dispute)
    assert dispute.status == "FRAUD_BLOCKED"


def test_assign_escalation(db_session):
    service = EscalationService(db_session)
    dispute = db_session.query(Dispute).first()
    esc = Escalation(
        dispute_id=dispute.id,
        reason="General review",
        priority="MEDIUM",
        status="OPEN",
    )
    db_session.add(esc)
    db_session.commit()

    res = service.assign_escalation(
        escalation_id=esc.id,
        assigned_to="SUPERVISOR_SPECIALIST_3",
        supervisor_id="SUP_LEAD",
    )
    assert res.action == "ASSIGN"
    db_session.refresh(esc)
    assert esc.assigned_to == "SUPERVISOR_SPECIALIST_3"
    assert esc.status == "IN_REVIEW"


def test_sla_breach_detection_and_filtering(db_session):
    service = EscalationService(db_session)
    dispute = db_session.query(Dispute).first()
    now = datetime.now(timezone.utc)

    # Breached ticket
    breached_esc = Escalation(
        dispute_id=dispute.id,
        reason="Past deadline escalation",
        priority="CRITICAL",
        assigned_to="OFFICER_A",
        sla_deadline=now - timedelta(hours=2),
        status="OPEN",
        created_at=now - timedelta(hours=6),
    )
    # Active ticket
    active_esc = Escalation(
        dispute_id=dispute.id,
        reason="Active normal ticket",
        priority="LOW",
        assigned_to="OFFICER_B",
        sla_deadline=now + timedelta(hours=8),
        status="OPEN",
        created_at=now,
    )
    db_session.add_all([breached_esc, active_esc])
    db_session.commit()

    listing = service.list_escalations()
    assert listing.sla_breached_count >= 1

    breached_item = next(i for i in listing.items if i.id == breached_esc.id)
    assert breached_item.is_sla_breached is True
    assert breached_item.hours_to_sla < 0

    # Test filtering by priority
    crit_listing = service.list_escalations(priority="CRITICAL")
    assert all(i.priority == "CRITICAL" for i in crit_listing.items)

    # Test filtering by assigned_to
    officer_b_listing = service.list_escalations(assigned_to="OFFICER_B")
    assert all(i.assigned_to == "OFFICER_B" for i in officer_b_listing.items)
