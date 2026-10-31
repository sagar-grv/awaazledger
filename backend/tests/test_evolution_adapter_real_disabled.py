"""Unit tests for Evolution WhatsApp Adapter normalization and offline fallbacks."""

import pytest
from app.channels.evolution_whatsapp_adapter import EvolutionWhatsAppAdapter
from app.core.config import settings


def test_evolution_send_text_mocked_when_disabled(monkeypatch):
    """Verifies send_text returns MOCKED status when live Evolution is disabled."""
    monkeypatch.setattr(settings, "ENABLE_EVOLUTION_LIVE", False)
    adapter = EvolutionWhatsAppAdapter()
    res = adapter.send_text("+919876543210", "Hello Test")

    assert res["status"] in ("MOCKED", "SUCCESS")
    assert res["channel"] == "WHATSAPP_EVOLUTION"
    assert res["recipient"] == "+919876543210"


def test_evolution_normalize_audio_message():
    """Verifies audioMessage payload is normalized to voice message_type."""
    adapter = EvolutionWhatsAppAdapter()
    payload = {
        "event": "messages.upsert",
        "instance": "paytm-awaazledger",
        "data": {
            "key": {
                "remoteJid": "919876543210@s.whatsapp.net",
                "id": "MSG-AUDIO-9988",
            },
            "message": {
                "audioMessage": {
                    "url": "https://example.com/audio.ogg",
                    "mimetype": "audio/ogg",
                    "caption": "Voice note regarding payment",
                }
            },
            "messageTimestamp": 1700000000,
        },
    }

    norm = adapter.handle_incoming_payload(payload)
    assert norm["channel"] == "WHATSAPP_EVOLUTION"
    assert norm["phone"] == "+919876543210"
    assert norm["message_type"] == "voice"
    assert norm["is_voice"] is True
    assert norm["media_url"] == "https://example.com/audio.ogg"
    assert norm["message_id"] == "MSG-AUDIO-9988"


def test_evolution_normalize_image_message():
    """Verifies imageMessage payload is normalized to image message_type."""
    adapter = EvolutionWhatsAppAdapter()
    payload = {
        "event": "messages.upsert",
        "instance": "paytm-awaazledger",
        "data": {
            "key": {
                "remoteJid": "919876543211@s.whatsapp.net",
                "id": "MSG-IMG-1122",
            },
            "message": {
                "imageMessage": {
                    "url": "https://example.com/receipt.jpg",
                    "mimetype": "image/jpeg",
                    "caption": "Screenshot of debit SMS",
                }
            },
            "messageTimestamp": 1700000010,
        },
    }

    norm = adapter.handle_incoming_payload(payload)
    assert norm["channel"] == "WHATSAPP_EVOLUTION"
    assert norm["phone"] == "+919876543211"
    assert norm["message_type"] == "image"
    assert norm["is_image"] is True
    assert norm["media_url"] == "https://example.com/receipt.jpg"
    assert norm["message_id"] == "MSG-IMG-1122"


def test_evolution_phone_cleaning():
    """Verifies clean recipient removes special characters for API payload."""
    adapter = EvolutionWhatsAppAdapter()
    cleaned = adapter._clean_recipient("+91 (987) 654-3210")
    assert cleaned == "919876543210"
