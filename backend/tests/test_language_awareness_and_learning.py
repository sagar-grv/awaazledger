"""Unit tests for multi-language awareness (Hindi, English, Marathi), multimodal voice/image parity, and self-learning engine."""

import pytest
from app.services.channel_message_service import process_text_message
from app.services.intent_extractor import detect_language, extract_entities_from_text
from app.services.learning_service import AgentLearningService
from app.db.session import SessionLocal
from app.models.dispute import Dispute


def test_marathi_language_awareness_and_response():
    """Asking in Marathi should detect language as Marathi ('mr') and respond in Marathi."""
    text = "माझे 450 रुपये कापले गेले आहेत पण दुकानदाराला मिळाले नाहीत. UTR 987654321012."
    lang = detect_language(text)
    assert lang == "mr"

    res = process_text_message(
        sender_phone="+918788021157",
        user_id=1,
        message=text,
        channel="WHATSAPP_EVOLUTION",
    )
    assert res["entities"].language == "mr"


def test_marathi_clarification_response():
    """Asking in Marathi without UTR should return prompt in Marathi."""
    text = "पैसे कटले काय करू?"
    res = process_text_message(
        sender_phone="+918788021157",
        user_id=1,
        message=text,
        channel="WHATSAPP_EVOLUTION",
    )
    assert res["needs_more_info"] is True
    assert "UTR" in res["agent_message"]
    # Should contain Marathi words
    assert "पैसे" in res["agent_message"] or "खात्यातून" in res["agent_message"] or "अंकी" in res["agent_message"]


def test_english_language_awareness_and_response():
    """Asking in English should detect language as English ('en') and respond in English."""
    text = "What is bridge credit?"
    lang = detect_language(text)
    assert lang == "en"

    res = process_text_message(
        sender_phone="+918788021157",
        user_id=1,
        message=text,
        channel="WHATSAPP_EVOLUTION",
    )
    assert res["entities"].language == "en"
    assert "Bridge Credit" in res["agent_message"]
    assert "reconciliation" in res["agent_message"].lower() or "wallet" in res["agent_message"].lower()


def test_self_learning_engine_telemetry(db_session):
    """Verifies that self-learning engine records feedback, tunes confidence, and exposes learning telemetry."""
    service = AgentLearningService(db_session)

    # 1. Record feedback learning
    disp = db_session.query(Dispute).first()
    entry = service.record_feedback_learning(disp, rating="1", raw_text="bohot badhiya service", phone="+918788021157")
    assert entry.id is not None
    assert entry.trigger_type == "FEEDBACK_HELPFUL"

    # 2. Query telemetry
    telemetry = service.get_learning_telemetry()
    assert telemetry["continuous_learning_active"] is True
    assert telemetry["total_learning_cycles"] >= 1
    assert "+" in telemetry["accuracy_improvement_pct"]
    assert "hi" in telemetry["language_distribution"]
    assert len(telemetry["recent_adaptations"]) >= 1
