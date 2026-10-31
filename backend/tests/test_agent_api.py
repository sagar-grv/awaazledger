"""Tests for agent and dispute API endpoints."""

import pytest
from app.api.disputes import create_dispute, list_disputes, get_dispute
from app.api.agent import run_agent_on_dispute, run_agent_by_code, get_agent_state
from app.schemas.dispute import DisputeCreateRequest, DisputeStatus, AgentDecision
from app.models.dispute import Dispute


def test_create_dispute_endpoint(db_session):
    payload = DisputeCreateRequest(
        user_id=1,
        utr="987654321012",
        claimed_amount=450.0,
        channel="WHATSAPP",
        intent="DEBIT_NO_CREDIT",
        language="hi",
        transcript="Mere 450 rupaye kat gaye par dukandar ko nahi mile.",
    )
    res = create_dispute(payload, db=db_session)
    assert res.id is not None
    assert res.utr == "987654321012"
    assert res.status == DisputeStatus.PENDING.value
    assert res.amount == 450.0


def test_list_and_get_disputes_endpoint(db_session):
    disputes = list_disputes(db=db_session)
    assert len(disputes) >= 5

    first_disp = disputes[0]
    fetched = get_dispute(first_disp.id, db=db_session)
    assert fetched.id == first_disp.id
    assert fetched.dispute_code == first_disp.dispute_code


def test_run_agent_by_code_endpoint(db_session):
    res = run_agent_by_code("DISP-SCN-01", db=db_session)
    assert res["dispute_code"] == "DISP-SCN-01"
    assert res["decision"] == AgentDecision.AUTO_RESOLVE.value
    assert res["resolved"] is True
    assert res["status"] == DisputeStatus.AUTO_CREDITED.value


def test_get_agent_state_endpoint(db_session):
    disp = db_session.query(Dispute).filter(Dispute.dispute_code == "DISP-SCN-01").first()
    state_info = get_agent_state(disp.id, db=db_session)
    assert state_info.dispute_id == disp.id
    assert state_info.current_state in [
        DisputeStatus.AUTO_CREDITED.value,
        DisputeStatus.RESOLVED.value,
        DisputeStatus.PENDING.value,
    ]
    assert len(state_info.history) > 0
