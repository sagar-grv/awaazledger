"""Unit tests for WhatsApp and Simulator channel adapters."""

import pytest
from app.channels.simulator_adapter import SimulatorAdapter
from app.channels.evolution_whatsapp_adapter import EvolutionWhatsAppAdapter
from app.channels.channel_router import get_adapter


def test_simulator_adapter_send_text():
    adapter = SimulatorAdapter()
    res = adapter.send_text("+919876543210", "Aapka dispute process ho gaya hai.")
    assert res["status"] == "SUCCESS"
    assert res["channel"] == "SIMULATOR"


def test_evolution_whatsapp_adapter_unconfigured_mock():
    adapter = EvolutionWhatsAppAdapter(base_url="http://localhost:8080", api_key="")
    res = adapter.send_text("+919876543210", "Hello via Evolution")
    assert res["status"] == "MOCKED"
    assert "not configured" in res["reason"]


def test_evolution_payload_normalization():
    adapter = EvolutionWhatsAppAdapter()
    raw_payload = {
        "event": "messages.upsert",
        "instance": "paytm-awaazledger",
        "data": {
            "key": {
                "remoteJid": "919876543210@s.whatsapp.net",
                "fromMe": False,
                "id": "MSG-EVO-12345",
            },
            "message": {
                "conversation": "Mera 450 rupaye kat gaya UTR 987654321012",
            },
        },
    }

    normalized = adapter.handle_incoming_payload(raw_payload)
    assert normalized["channel"] == "WHATSAPP_EVOLUTION"
    assert normalized["phone"] == "+919876543210"
    assert normalized["message_type"] == "text"
    assert "987654321012" in normalized["text"]
    assert normalized["message_id"] == "MSG-EVO-12345"


def test_channel_router():
    assert isinstance(get_adapter("SIMULATOR"), SimulatorAdapter)
    assert isinstance(get_adapter("WHATSAPP_EVOLUTION"), EvolutionWhatsAppAdapter)
    assert isinstance(get_adapter("WHATSAPP"), EvolutionWhatsAppAdapter)
