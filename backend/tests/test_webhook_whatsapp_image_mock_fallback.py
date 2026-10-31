"""Unit tests for WhatsApp Evolution webhook image OCR processing and mock fallback."""

import pytest
from app.api.webhooks import process_whatsapp_payload
from app.core.config import settings


def test_webhook_whatsapp_image_mock_fallback(monkeypatch, db_session):
    """Test image receipt processing falls back to mock OCR when real OCR is disabled."""
    monkeypatch.setattr(settings, "ENABLE_OCR_REAL", False)

    payload = {
        "event": "messages.upsert",
        "instance": "paytm-awaazledger",
        "data": {
            "key": {
                "remoteJid": "919876543210@s.whatsapp.net",
                "id": "MSG-IMAGE-FALLBACK-001",
            },
            "message": {
                "imageMessage": {
                    "url": "https://example.com/screenshot_scn01_valid.jpg",
                    "mimetype": "image/jpeg",
                    "caption": "screenshot_scn01_valid.jpg",
                }
            },
            "messageTimestamp": 1700000030,
        },
    }

    res = process_whatsapp_payload(payload, db=db_session)
    assert res["status"] == "SUCCESS"
    assert res["dispute_id"] is not None
    assert res["decision"] == "AUTO_RESOLVE"
