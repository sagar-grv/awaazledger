"""Unit tests for WhatsApp feedback parsing, persistence, and automated escalations."""

import pytest
from app.services.feedback_service import FeedbackService
from app.models.dispute import Dispute
from app.models.escalation import Escalation


def test_parse_whatsapp_feedback_ratings(db_session):
    """Test mapping user text input to canonical feedback ratings."""
    svc = FeedbackService(db_session)

    assert svc.parse_whatsapp_feedback("1") == "HELPFUL"
    assert svc.parse_whatsapp_feedback("helpful") == "HELPFUL"
    assert svc.parse_whatsapp_feedback("haan bahut sahi") == "HELPFUL"

    assert svc.parse_whatsapp_feedback("2") == "NOT_HELPFUL"
    assert svc.parse_whatsapp_feedback("not helpful") == "NOT_HELPFUL"
    assert svc.parse_whatsapp_feedback("nahi hua") == "NOT_HELPFUL"

    assert svc.parse_whatsapp_feedback("3") == "HUMAN_REQUEST"
    assert svc.parse_whatsapp_feedback("human") == "HUMAN_REQUEST"
    assert svc.parse_whatsapp_feedback("operator se baat karao") == "HUMAN_REQUEST"

    assert svc.parse_whatsapp_feedback("4") == "WRONG_DECISION"
    assert svc.parse_whatsapp_feedback("wrong decision") == "WRONG_DECISION"
    assert svc.parse_whatsapp_feedback("galat faisla") == "WRONG_DECISION"

    assert svc.parse_whatsapp_feedback("unrelated sentence") is None


def test_feedback_registration_and_consumption(db_session):
    """Test full feedback lifecycle: register pending -> consume -> verify record."""
    svc = FeedbackService(db_session)
    phone = "+919876543210"

    disp = db_session.query(Dispute).first()
    assert disp is not None

    svc.register_pending_feedback(phone, disp.id)
    assert svc.has_pending_feedback(phone) is True

    fb = svc.consume_feedback(phone, "1")
    assert fb is not None
    assert fb.rating == "HELPFUL"
    assert fb.dispute_id == disp.id
    assert svc.has_pending_feedback(phone) is False


def test_feedback_human_request_triggers_escalation(db_session):
    """Test that customer replying '3' (human) automatically creates an escalation."""
    svc = FeedbackService(db_session)
    phone = "+919876543211"

    disp = db_session.query(Dispute).filter(Dispute.id == 1).first()
    assert disp is not None

    svc.register_pending_feedback(phone, disp.id)
    fb = svc.consume_feedback(phone, "3 - talk to human")

    assert fb is not None
    assert fb.rating == "HUMAN_REQUEST"

    # Verify escalation created
    esc = db_session.query(Escalation).filter(Escalation.dispute_id == disp.id).first()
    assert esc is not None
    assert "CUSTOMER_REQUESTED_HUMAN" in esc.reason
