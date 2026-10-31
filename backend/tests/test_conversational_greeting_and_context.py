"""Unit tests verifying initial greeting welcome message and multi-turn conversational context."""

import pytest
from app.services.channel_message_service import process_text_message, _CONVERSATION_SESSIONS
from app.schemas.ingest import IntentType
from app.db.session import SessionLocal
from app.models.dispute import Dispute


def test_initial_greeting_welcome_message():
    """Sending 'hii' or greeting should return a warm introductory welcome message with user name."""
    res = process_text_message(
        sender_phone="+918788021157",
        user_id=1,
        message="hii",
        channel="WHATSAPP_EVOLUTION",
    )
    assert res["needs_more_info"] is True
    assert res["dispute_id"] is None
    assert res["entities"].intent == IntentType.GREETING
    # Must contain greeting, user name or respectful address, and mention of UPI / UTR
    assert "Paytm AwaazLedger" in res["agent_message"]
    assert "UTR" in res["agent_message"]
    assert "नमस्ते" in res["agent_message"] or "Hello" in res["agent_message"]


def test_multiturn_context_continuity():
    """Turn 1: User says money was deducted with amount. Turn 2: User provides UTR. Dispute inherits amount."""
    phone = "+918788021157"

    # Turn 1: "mere 450 rupees cut gaye mai kya karu ?"
    turn1 = process_text_message(
        sender_phone=phone,
        user_id=1,
        message="mere 450 rupees cut gaye mai kya karu ?",
        channel="WHATSAPP_EVOLUTION",
    )
    assert turn1["needs_more_info"] is True
    assert turn1["dispute_id"] is None
    assert turn1["entities"].amount == 450.0
    assert "450" in turn1["agent_message"]
    assert "UTR" in turn1["agent_message"]

    # Turn 2: User sends just the UTR
    turn2 = process_text_message(
        sender_phone=phone,
        user_id=1,
        message="UTR 987654321012",
        channel="WHATSAPP_EVOLUTION",
    )
    assert turn2["needs_more_info"] is False
    assert turn2["dispute_id"] is not None
    assert turn2["entities"].utr == "987654321012"
    # Verify dispute in DB inherited the claimed amount 450.0
    db = SessionLocal()
    try:
        disp = db.query(Dispute).filter(Dispute.id == turn2["dispute_id"]).first()
        assert disp is not None
        assert disp.claimed_amount == 450.0
    finally:
        db.close()


def test_invalid_utr_response():
    """Providing a short or malformed UTR string should explain 12-digit requirement."""
    res = process_text_message(
        sender_phone="+918788021157",
        user_id=1,
        message="Mera UTR 123 hai",
        channel="WHATSAPP_EVOLUTION",
    )
    assert res["needs_more_info"] is True
    assert res["entities"].intent == IntentType.INVALID_UTR
    assert "12" in res["agent_message"]
    assert "UTR" in res["agent_message"]


def test_faq_pin_reset():
    """Asking how to reset UPI pin should provide safe step-by-step guidance."""
    res = process_text_message(
        sender_phone="+918788021157",
        user_id=1,
        message="UPI PIN kaise reset kare?",
        channel="WHATSAPP_EVOLUTION",
    )
    assert res["needs_more_info"] is True
    assert res["entities"].intent == IntentType.FAQ_PIN_RESET
    assert "PIN" in res["agent_message"]


def test_faq_bridge_credit():
    """Asking what bridge credit is should explain the provisional wallet credit mechanism."""
    res = process_text_message(
        sender_phone="+918788021157",
        user_id=1,
        message="Bridge credit kya hota hai?",
        channel="WHATSAPP_EVOLUTION",
    )
    assert res["needs_more_info"] is True
    assert res["entities"].intent == IntentType.FAQ_BRIDGE_CREDIT
    assert "Bridge Credit" in res["agent_message"]


def test_faq_refund_tat():
    """Asking when money will be refunded should return standard RBI TAT and delay penalty details."""
    res = process_text_message(
        sender_phone="+918788021157",
        user_id=1,
        message="Paisa kab tak aayega kitne din lagenge?",
        channel="WHATSAPP_EVOLUTION",
    )
    assert res["needs_more_info"] is True
    assert res["entities"].intent == IntentType.FAQ_REFUND_TAT
    assert "T+1" in res["agent_message"] or "T+5" in res["agent_message"] or "RBI" in res["agent_message"]


def test_out_of_scope_query():
    """Asking out of scope questions (e.g. weather, movies) should politely redirect to UPI dispute assistance."""
    res = process_text_message(
        sender_phone="+918788021157",
        user_id=1,
        message="Aaj ka weather kaisa hai?",
        channel="WHATSAPP_EVOLUTION",
    )
    assert res["needs_more_info"] is True
    assert res["entities"].intent == IntentType.OUT_OF_SCOPE
    assert "UPI" in res["agent_message"] or "Paytm" in res["agent_message"]
