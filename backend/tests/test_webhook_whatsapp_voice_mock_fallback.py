"""Unit tests for WhatsApp Evolution webhook voice processing and mock fallback."""

import pytest
from app.api.webhooks import process_whatsapp_payload
from app.core.config import settings


def test_webhook_whatsapp_voice_mock_fallback(monkeypatch, db_session):
    """Test voice message processing falls back to mock STT when real Sarvam is disabled."""
    monkeypatch.setattr(settings, "ENABLE_SARVAM_REAL", False)

    payload = {
        "event": "messages.upsert",
        "instance": "paytm-awaazledger",
        "data": {
            "key": {
                "remoteJid": "919876543210@s.whatsapp.net",
                "id": "MSG-VOICE-FALLBACK-001",
            },
            "message": {
                "audioMessage": {
                    "url": "https://example.com/voice_hindi_scn01.ogg",
                    "mimetype": "audio/ogg",
                    "caption": "voice_hindi_scn01.ogg",
                }
            },
            "messageTimestamp": 1700000020,
        },
    }

    res = process_whatsapp_payload(payload, db=db_session)
    assert res["status"] == "SUCCESS"
    assert res["dispute_id"] is not None
    assert res["decision"] == "AUTO_RESOLVE"
