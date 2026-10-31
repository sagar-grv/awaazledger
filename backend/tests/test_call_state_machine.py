"""Unit tests for CallDialogManager and Voice Call AI Teammate state machine."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models.user import User
from app.models.transaction import Transaction
from app.models.call_session import CallSession
from app.models.call_turn import CallTurn
from app.models.call_feedback import CallFeedback
from app.calls.call_state_machine import CallDialogManager, normalize_spoken_digits
from app.core.config import settings


@pytest.fixture
def test_db(monkeypatch):
    monkeypatch.setattr(settings, "ENABLE_SARVAM_REAL", False)
    monkeypatch.setattr(settings, "ENABLE_EVOLUTION_LIVE", False)
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine)
    session = TestingSession()

    user = User(
        id=1,
        name="Rohit Sharma",
        mobile_hash="hash_8788021157",
        paytm_id="rohit@paytm",
        language="hi",
        trust_score=90,
    )
    session.add(user)

    txn = Transaction(
        utr="987654321012",
        user_id=1,
        amount=450.0,
        merchant_name="Sharma Kirana",
        cbs_status="DEBIT_SUCCESS",
        npcI_status="DEEMED_APPROVED",
        beneficiary_status="NOT_CREDITED",
    )
    session.add(txn)
    session.commit()

    yield session
    session.close()


def test_normalize_spoken_digits():
    text = "nau aath saat chhe paanch chaar teen do ek shunya ek do"
    digits = normalize_spoken_digits(text)
    assert digits == "987654321012"

    text_en = "nine eight seven six five four three two one zero one two"
    digits_en = normalize_spoken_digits(text_en)
    assert digits_en == "987654321012"


def test_call_consent_grant_flow(test_db):
    call = CallSession(
        call_sid="CALL-TEST01",
        channel="BROWSER_WEBRTC",
        caller_phone="+918788021157",
        user_id=1,
        language="hi",
        current_state="GREETING_CONSENT",
    )
    test_db.add(call)
    test_db.commit()

    mgr = CallDialogManager(test_db, call)
    greeting = mgr.get_initial_greeting()
    assert greeting["current_state"] == "GREETING_CONSENT"
    assert "Paytm AwaazLedger" in greeting["agent_speech"]

    # Caller grants consent
    res = mgr.process_turn(caller_transcript="हाँ, मैं सहमत हूँ।")
    assert res["current_state"] == "COLLECT_ISSUE_UTR"
    assert call.consent_given is True


def test_call_consent_refusal_flow(test_db):
    call = CallSession(
        call_sid="CALL-TEST02",
        channel="BROWSER_WEBRTC",
        caller_phone="+918788021157",
        user_id=1,
        language="hi",
        current_state="GREETING_CONSENT",
    )
    test_db.add(call)
    test_db.commit()

    mgr = CallDialogManager(test_db, call)
    res = mgr.process_turn(caller_transcript="नहीं, मुझे रिकॉर्डिंग नहीं चाहिए।")
    assert res["current_state"] == "ENDED"
    assert res["is_final"] is True
    assert call.consent_given is False


def test_call_end_to_end_instant_credit(test_db):
    call = CallSession(
        call_sid="CALL-TEST03",
        channel="BROWSER_WEBRTC",
        caller_phone="+918788021157",
        user_id=1,
        language="hi",
        current_state="GREETING_CONSENT",
    )
    test_db.add(call)
    test_db.commit()

    mgr = CallDialogManager(test_db, call)
    mgr.process_turn(dtmf_digit="1")  # Consent granted via DTMF

    # Caller reports dispute with UTR and amount
    res = mgr.process_turn(caller_transcript="Bhaiya 450 rupaye kat gaye dukandar ko nahi mila. UTR 987654321012")
    assert res["current_state"] == "COLLECT_FEEDBACK"
    assert res["dispute_code"] is not None
    assert res["claimed_amount"] == 450.0

    # Caller provides feedback
    fb_res = mgr.process_turn(dtmf_digit="1")
    assert fb_res["current_state"] == "ENDED"
    assert fb_res["is_final"] is True


def test_call_missing_utr_fallback(test_db):
    call = CallSession(
        call_sid="CALL-TEST04",
        channel="BROWSER_WEBRTC",
        caller_phone="+918788021157",
        user_id=1,
        language="hi",
        current_state="COLLECT_ISSUE_UTR",
        consent_given=True,
    )
    test_db.add(call)
    test_db.commit()

    mgr = CallDialogManager(test_db, call)
    res = mgr.process_turn(caller_transcript="Mujhe UTR nahi pata, SMS delete ho gaya")
    assert res["current_state"] == "COLLECT_FEEDBACK"
    assert "WhatsApp" in res["agent_speech"]
