"""Unit tests for WhatsApp Evolution webhook text ingestion and idempotency."""

import pytest
from app.api.webhooks import process_whatsapp_payload, get_whatsapp_webhook_health


def test_webhook_whatsapp_text_success(db_session):
    """Test processing valid WhatsApp text complaint creates dispute and runs agent."""
    payload = {
        "event": "messages.upsert",
        "instance": "paytm-awaazledger",
        "data": {
            "key": {
                "remoteJid": "919876543210@s.whatsapp.net",
                "id": "MSG-TEST-TEXT-001",
            },
            "message": {
                "conversation": "Mera 450 rupaye kat gaya shopkeeper ko nahi mila. UTR 987654321012",
            },
            "messageTimestamp": 1700000000,
        },
    }

    res = process_whatsapp_payload(payload, db=db_session)
    assert res["status"] == "SUCCESS"
    assert res["dispute_id"] is not None
    assert res["dispute_code"].startswith("DISP-")
    assert res["decision"] == "AUTO_RESOLVE"


def test_webhook_whatsapp_text_idempotency(db_session):
    """Test duplicate message_id is detected and skipped without creating duplicate disputes."""
    payload = {
        "event": "messages.upsert",
        "instance": "paytm-awaazledger",
        "data": {
            "key": {
                "remoteJid": "919876543210@s.whatsapp.net",
                "id": "MSG-DUPLICATE-CHECK-999",
            },
            "message": {
                "conversation": "Mera 450 rupaye kat gaya UTR 987654321012",
            },
            "messageTimestamp": 1700000001,
        },
    }

    res1 = process_whatsapp_payload(payload, db=db_session)
    assert res1["status"] == "SUCCESS"

    res2 = process_whatsapp_payload(payload, db=db_session)
    assert res2["status"] == "DUPLICATE"
    assert res2["message_id"] == "MSG-DUPLICATE-CHECK-999"


def test_webhook_health_endpoint():
    """Test GET /api/v1/webhooks/whatsapp/health diagnostic response."""
    health = get_whatsapp_webhook_health()
    assert health["status"] == "HEALTHY"
    assert "whatsapp_mode" in health
    assert "evolution_api_url" in health
    assert "feedback_enabled" in health
