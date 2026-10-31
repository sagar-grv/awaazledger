"""Tests for escalation endpoints."""

import pytest
from app.api.escalations import (
    list_escalations,
    get_escalation_detail,
    approve_escalation,
    reject_escalation,
    request_info_escalation,
    mark_fraud_escalation,
    assign_escalation,
    resolve_escalation,
)
from app.models.dispute import Dispute
from app.models.escalation import Escalation
from app.schemas.escalation import (
    SupervisorActionRequest,
    SupervisorAssignRequest,
    EscalationResolveRequest,
)


def test_api_list_and_detail(db_session):
    dispute = db_session.query(Dispute).first()
    esc = Escalation(
        dispute_id=dispute.id,
        reason="API test escalation",
        priority="HIGH",
        status="OPEN",
    )
    db_session.add(esc)
    db_session.commit()

    listing = list_escalations(db=db_session)
    assert listing.total >= 1

    detail = get_escalation_detail(escalation_id=esc.id, db=db_session)
    assert detail.escalation.id == esc.id
    assert detail.dispute["id"] == dispute.id


def test_api_approve_endpoint(db_session):
    dispute = db_session.query(Dispute).filter(Dispute.dispute_code == "DISP-SCN-03").first()
    esc = Escalation(
        dispute_id=dispute.id,
        reason="API approve test",
        priority="HIGH",
        status="OPEN",
    )
    db_session.add(esc)
    db_session.commit()

    req = SupervisorActionRequest(note="Verified via phone call", supervisor_id="OPS_LEAD")
    res = approve_escalation(escalation_id=esc.id, payload=req, db=db_session)
    assert res.action == "APPROVE"
    assert res.status == "APPROVED"
    assert res.bridge_credit_id is not None


def test_api_reject_endpoint(db_session):
    dispute = db_session.query(Dispute).filter(Dispute.dispute_code == "DISP-SCN-04").first()
    esc = Escalation(
        dispute_id=dispute.id,
        reason="API reject test",
        priority="LOW",
        status="OPEN",
    )
    db_session.add(esc)
    db_session.commit()

    req = SupervisorActionRequest(action_reason="Invalid claim duplicate", supervisor_id="OPS_LEAD")
    res = reject_escalation(escalation_id=esc.id, payload=req, db=db_session)
    assert res.action == "REJECT"
    assert res.status == "REJECTED"


def test_api_request_info_and_mark_fraud(db_session):
    dispute = db_session.query(Dispute).first()
    esc1 = Escalation(dispute_id=dispute.id, reason="API info test", priority="LOW", status="OPEN")
    esc2 = Escalation(dispute_id=dispute.id, reason="API fraud test", priority="CRITICAL", status="OPEN")
    db_session.add_all([esc1, esc2])
    db_session.commit()

    info_req = SupervisorActionRequest(requested_info_prompt="Need IFSC code verification")
    res1 = request_info_escalation(escalation_id=esc1.id, payload=info_req, db=db_session)
    assert res1.action == "REQUEST_INFO"
    assert res1.status == "INFO_REQUESTED"

    fraud_req = SupervisorActionRequest(action_reason="Stolen credentials report")
    res2 = mark_fraud_escalation(escalation_id=esc2.id, payload=fraud_req, db=db_session)
    assert res2.action == "MARK_FRAUD"
    assert res2.status == "FRAUD_CONFIRMED"


def test_api_assign_and_legacy_resolve(db_session):
    dispute = db_session.query(Dispute).first()
    esc = Escalation(dispute_id=dispute.id, reason="API assign test", priority="MEDIUM", status="OPEN")
    db_session.add(esc)
    db_session.commit()

    assign_req = SupervisorAssignRequest(assigned_to="SUPERVISOR_99")
    res = assign_escalation(escalation_id=esc.id, payload=assign_req, db=db_session)
    assert res.action == "ASSIGN"
    assert res.status == "IN_REVIEW"

    # Legacy resolve
    legacy_req = EscalationResolveRequest(resolution_notes="Approved via legacy", approved=True)
    resolved = resolve_escalation(escalation_id=esc.id, payload=legacy_req, db=db_session)
    assert resolved.status == "APPROVED"
