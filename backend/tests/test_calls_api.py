"""Direct endpoint function tests for Calls API."""

import pytest
from app.api.calls import (
    initiate_call,
    process_call_turn,
    send_dtmf_digit,
    end_call,
    submit_call_feedback,
    get_live_calls,
    telephony_sip_webhook,
)
from app.api.metrics import get_voice_call_metrics
from app.schemas.call import (
    CallInitiateRequest,
    CallTurnRequest,
    CallDtmfRequest,
    CallFeedbackRequest,
)
from app.core.config import settings


def test_calls_api_direct_flow(db_session, monkeypatch):
    monkeypatch.setattr(settings, "ENABLE_SARVAM_REAL", False)
    monkeypatch.setattr(settings, "ENABLE_EVOLUTION_LIVE", False)

    # 1. Initiate Call
    init_req = CallInitiateRequest(
        caller_phone="+918788021157",
        language="hi",
        channel="BROWSER_WEBRTC",
    )
    init_res = initiate_call(req=init_req, db=db_session)
    call_sid = init_res.call_sid
    assert call_sid.startswith("CALL-")
    assert init_res.current_state == "GREETING_CONSENT"

    # 2. Grant Consent via DTMF
    turn1_req = CallDtmfRequest(digit="1")
    turn1 = send_dtmf_digit(call_sid=call_sid, req=turn1_req, db=db_session)
    assert turn1.current_state == "COLLECT_ISSUE_UTR"

    # 3. Report Dispute via Spoken Transcript
    turn2_req = CallTurnRequest(transcript="Bhaiya 450 kat gaye UTR 987654321012")
    turn2 = process_call_turn(call_sid=call_sid, req=turn2_req, db=db_session)
    assert turn2.current_state == "COLLECT_FEEDBACK"
    assert turn2.dispute_code is not None

    # 4. Feedback
    fb_req = CallFeedbackRequest(rating="HELPFUL", feedback_type="VOICE")
    fb_res = submit_call_feedback(call_sid=call_sid, req=fb_req, db=db_session)
    assert fb_res["status"] == "SUCCESS"

    # 5. Live Calls
    live = get_live_calls(db=db_session)
    assert any(c["call_sid"] == call_sid for c in live)

    # 6. Call Metrics
    m = get_voice_call_metrics(db=db_session)
    assert m["total_calls"] >= 1

    # 7. End Call
    ended = end_call(call_sid=call_sid, db=db_session)
    assert ended.status == "COMPLETED"


def test_telephony_sip_webhook(db_session, monkeypatch):
    monkeypatch.setattr(settings, "ENABLE_SARVAM_REAL", False)
    monkeypatch.setattr(settings, "ENABLE_EVOLUTION_LIVE", False)

    # Inbound call
    payload1 = {"caller": "+918788021157"}
    res1 = telephony_sip_webhook(payload=payload1, db=db_session)
    assert res1["status"] == "INITIATED"
    call_sid = res1["call_sid"]

    # Inbound DTMF digit
    payload2 = {"call_sid": call_sid, "Digits": "1"}
    res2 = telephony_sip_webhook(payload=payload2, db=db_session)
    assert res2["status"] == "IN_PROGRESS"
