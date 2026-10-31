"""Tests for feature-flagged real connectors and deterministic mock fallbacks."""

import pytest
from app.services.voice_ingestion_service import transcribe_voice
from app.services.ocr_service import extract_ocr_from_image
from app.channels.evolution_whatsapp_adapter import EvolutionWhatsAppAdapter
from app.core.config import settings


def test_voice_fallback_when_real_sarvam_disabled(monkeypatch):
    """When ENABLE_SARVAM_REAL is False, transcribe_voice returns mock fallback."""
    monkeypatch.setattr(settings, "ENABLE_SARVAM_REAL", False)
    res = transcribe_voice("voice_hindi_scn01.ogg", b"fake_audio_bytes")

    assert res["transcript"] != ""
    assert res["source"] in ("MOCK_SARVAM_FALLBACK", "MOCK_FILENAME_MATCH")
    assert "987654321012" in res["transcript"]


def test_ocr_fallback_when_real_ocr_disabled(monkeypatch):
    """When ENABLE_OCR_REAL is False, extract_ocr_from_image returns mock fallback."""
    monkeypatch.setattr(settings, "ENABLE_OCR_REAL", False)
    res = extract_ocr_from_image("screenshot_scn01_valid.jpg", b"fake_image_bytes")

    assert res["source"] in ("MOCK_OCR_FALLBACK", "MOCK_FILENAME_MATCH")
    assert res["ocr_json"]["utr"] == "987654321012"
    assert res["ocr_json"]["amount"] == 450.0


def test_evolution_whatsapp_fallback_when_live_disabled(monkeypatch):
    """When ENABLE_EVOLUTION_LIVE is False, EvolutionWhatsAppAdapter falls back safely."""
    monkeypatch.setattr(settings, "ENABLE_EVOLUTION_LIVE", False)
    adapter = EvolutionWhatsAppAdapter()
    res = adapter.send_text("+919876543210", "Hello from AwaazLedger")

    assert res["status"] in ("MOCKED", "FALLBACK_SIMULATOR")
    assert "not configured" in res["reason"]
