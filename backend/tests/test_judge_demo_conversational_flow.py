"""Tests for Judge Demo conversational flow, dynamic context understanding, and audit logging first."""

import pytest
from app.db.session import SessionLocal
from app.schemas.ingest import IntentType
from app.services.intent_extractor import extract_entities_from_text, extract_merchant_context
from app.services.channel_message_service import process_text_message, _build_context_response_message
from app.models.audit_log import AuditLog
from app.models.dispute import Dispute


def test_merchant_context_extraction():
    """Verifies that merchant entities are extracted from conversational text."""
    res = extract_merchant_context("Bhaiya 450 rupaye kat gaye, par dukandar ko nahi mila")
    assert res is not None
    assert "दुकानदार" in res

    res2 = extract_merchant_context("Paid 500 at petrol pump but transaction pending")
    assert res2 is not None
    assert "पेट्रोल पंप" in res2

    res3 = extract_merchant_context("Swiggy order failed, 320 debited")
    assert res3 is not None
    assert "Swiggy" in res3


def test_judge_demo_greeting_flow():
    """Verifies that initial greeting provides the complete hackathon judge demo intro and test examples."""
    user_info = {"name": "Sagar", "language": "hi"}
    
    # 1. Hindi Greeting
    entities_hi = extract_entities_from_text("Namaste", default_language="hi")
    assert entities_hi.intent == IntentType.GREETING
    msg_hi = _build_context_response_message(user_info, entities_hi, "Namaste")
    assert "Paytm AwaazLedger" in msg_hi
    assert "Judges Demo" in msg_hi
    assert "987654321012" in msg_hi
    assert "Sarvam AI" in msg_hi
    assert "Bridge credit kya hota hai" in msg_hi

    # 2. English Greeting
    user_en = {"name": "Sagar", "language": "en"}
    entities_en = extract_entities_from_text("Hello", default_language="en")
    msg_en = _build_context_response_message(user_en, entities_en, "Hello")
    assert "Paytm AwaazLedger" in msg_en
    assert "Judges Demo" in msg_en
    assert "What is bridge credit" in msg_en

    # 3. Marathi Greeting
    user_mr = {"name": "Sagar", "language": "mr"}
    entities_mr = extract_entities_from_text("Namaskar", default_language="mr")
    msg_mr = _build_context_response_message(user_mr, entities_mr, "Namaskar")
    assert "Paytm AwaazLedger" in msg_mr
    assert "Judges Demo" in msg_mr


def test_dynamic_context_understanding_without_utr():
    """Verifies that when user explains problem without UTR, AI addresses specific amount and merchant."""
    db = SessionLocal()
    try:
        # User message: "mere 450 rupees cut gaye mai kya karu ?"
        res = process_text_message(
            sender_phone="+918788021157",
            user_id=None,
            message="mere 450 rupees cut gaye mai kya karu ?",
            channel="WHATSAPP_EVOLUTION",
            db=db,
        )
        assert res["needs_more_info"] is True
        msg = res["agent_message"]
        # Must mention the exact amount (₹450) and ask for 12-digit UTR
        assert "450" in msg
        assert "UTR" in msg
        assert res["entities"].amount == 450.0
    finally:
        db.close()


def test_out_of_context_handling():
    """Verifies that out-of-context questions are addressed gracefully without crashing or robotic errors."""
    db = SessionLocal()
    try:
        res = process_text_message(
            sender_phone="+918788021157",
            user_id=None,
            message="aaj ka mausam kaisa hai?",
            channel="WHATSAPP_EVOLUTION",
            db=db,
        )
        assert res["needs_more_info"] is True
        msg = res["agent_message"]
        assert "Paytm AwaazLedger" in msg
        assert "UPI" in msg
    finally:
        db.close()


def test_audit_logging_first_before_resolution():
    """Verifies that when UTR is given, audit log is written to the database first."""
    db = SessionLocal()
    try:
        res = process_text_message(
            sender_phone="+918788021157",
            user_id=None,
            message="Bhaiya 450 rupaye kat gaye, par dukandar ko nahi mila. UTR 987654321012",
            channel="WHATSAPP_EVOLUTION",
            db=db,
        )
        assert res["needs_more_info"] is False
        dispute_id = res["dispute_id"]
        assert dispute_id is not None

        # Check that audit log entry was created for dispute intake
        audit_entry = db.query(AuditLog).filter(
            AuditLog.dispute_id == dispute_id,
            AuditLog.event == "DISPUTE_LOGGED_AND_REGISTERED",
        ).first()
        assert audit_entry is not None
        assert audit_entry.actor == "CHANNEL_INGESTION"

        # Check response message contains audit confirmation
        msg = res["agent_message"]
        assert "ऑडिट लॉग दर्ज किया गया" in msg or "Audit Log Recorded" in msg
    finally:
        db.close()


def test_gratitude_and_acknowledgment():
    """Verifies that user saying 'thanks' or 'ok' receives natural warm replies rather than errors."""
    db = SessionLocal()
    try:
        # 1. Test "thanks"
        res_thanks = process_text_message(
            sender_phone="+918788021157",
            user_id=None,
            message="thanks",
            channel="WHATSAPP_EVOLUTION",
            db=db,
        )
        assert res_thanks["needs_more_info"] is True
        msg_thanks = res_thanks["agent_message"]
        assert "स्वागत" in msg_thanks or "welcome" in msg_thanks.lower()
        # Must NOT be the fallback error!
        assert "पूरी तरह स्पष्ट नहीं हो पाया" not in msg_thanks

        # 2. Test "thank you so much" in English
        res_ty = process_text_message(
            sender_phone="+918788021157",
            user_id=None,
            message="thank you so much",
            channel="WHATSAPP_EVOLUTION",
            db=db,
        )
        msg_ty = res_ty["agent_message"]
        assert "welcome" in msg_ty.lower()
        assert "पूरी तरह स्पष्ट नहीं हो पाया" not in msg_ty

        # 3. Test "ok" or "theek hai"
        res_ok = process_text_message(
            sender_phone="+918788021157",
            user_id=None,
            message="theek hai",
            channel="WHATSAPP_EVOLUTION",
            db=db,
        )
        msg_ok = res_ok["agent_message"]
        assert "सहायता" in msg_ok or "assistance" in msg_ok.lower()
        assert "पूरी तरह स्पष्ट नहीं हो पाया" not in msg_ok
    finally:
        db.close()


def test_faq_knowledge_queries():
    """Verifies that the agent answers general customer support queries with rich knowledge."""
    db = SessionLocal()
    try:
        # 1. What is UTR
        res_utr = process_text_message(
            sender_phone="+918788021157",
            user_id=None,
            message="what is utr",
            channel="WHATSAPP_EVOLUTION",
            db=db,
        )
        msg_utr = res_utr["agent_message"]
        assert "Unique Transaction Reference" in msg_utr
        assert "12-digit" in msg_utr

        # 2. Why payment stuck
        res_stuck = process_text_message(
            sender_phone="+918788021157",
            user_id=None,
            message="why payment stuck",
            channel="WHATSAPP_EVOLUTION",
            db=db,
        )
        msg_stuck = res_stuck["agent_message"]
        assert "NPCI" in msg_stuck
        assert "Beneficiary" in msg_stuck

        # 3. UPI Limit
        res_lim = process_text_message(
            sender_phone="+918788021157",
            user_id=None,
            message="upi limit kitni hai",
            channel="WHATSAPP_EVOLUTION",
            db=db,
        )
        msg_lim = res_lim["agent_message"]
        assert "1,00,000" in msg_lim
    finally:
        db.close()

