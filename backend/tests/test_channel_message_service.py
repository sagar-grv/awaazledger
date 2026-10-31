"""Unit tests for unified channel message processor connecting input to dispute creation."""

from app.services.channel_message_service import (
    process_text_message,
    process_voice_message,
    process_image_message,
)
from app.db.session import SessionLocal
from app.models.dispute import Dispute


def test_process_text_message_creates_dispute():
    text = "Payment stuck INR 450 at kirana store. UTR 987654321012."
    res = process_text_message(
        sender_phone="+919876543210",
        user_id=1,
        message=text,
        channel="SIMULATOR",
    )
    assert res["needs_more_info"] is False
    assert res["dispute_id"] is not None
    assert res["dispute_code"].startswith("DISP-")

    db = SessionLocal()
    try:
        disp = db.query(Dispute).filter(Dispute.id == res["dispute_id"]).first()
        assert disp is not None
        assert disp.utr == "987654321012"
        assert disp.amount == 450.0
    finally:
        db.close()


def test_process_text_message_missing_utr_needs_info():
    text = "Mera payment fail ho gaya please refund."
    res = process_text_message(
        sender_phone="+919876543210",
        user_id=1,
        message=text,
        channel="SIMULATOR",
    )
    assert res["needs_more_info"] is True
    assert res["dispute_id"] is None
    assert "UTR" in res["agent_message"]


def test_process_voice_message_creates_dispute():
    res = process_voice_message(
        sender_phone="+919876543210",
        user_id=1,
        filename="voice_hindi_scn01.ogg",
        content=b"MOCK_BYTES",
        channel="SIMULATOR",
    )
    assert res["needs_more_info"] is False
    assert res["dispute_id"] is not None
    assert res["entities"].utr == "987654321012"


def test_process_image_message_creates_dispute():
    res = process_image_message(
        sender_phone="+919876543211",
        user_id=2,
        filename="screenshot_scn01_valid.jpg",
        content=b"MOCK_BYTES",
        channel="SIMULATOR",
    )
    assert res["needs_more_info"] is False
    assert res["dispute_id"] is not None
    assert res["entities"].utr == "987654321012"


def test_process_message_unknown_phone():
    res = process_text_message(
        sender_phone="+910000000000",
        user_id=None,
        message="Payment fail ho gaya UTR 987654321012",
        channel="WHATSAPP",
    )
    assert res["needs_more_info"] is True
    assert res["dispute_id"] is None
    assert "not registered" in res["agent_message"].lower()
