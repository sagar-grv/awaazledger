"""Unit tests for Sarvam STT network failure and safe fallback."""

import pytest
from app.services.voice_ingestion_service import transcribe_voice
from app.core.config import settings


def test_sarvam_stt_graceful_fallback_on_network_error(monkeypatch):
    """Verifies that if Sarvam API call fails or raises an exception, the service falls back."""
    monkeypatch.setattr(settings, "ENABLE_SARVAM_REAL", True)
    monkeypatch.setattr(settings, "SARVAM_API_KEY", "dummy_key")
    monkeypatch.setattr(settings, "SARVAM_STT_ENDPOINT", "http://invalid-non-existent-host:9999")

    # Should not raise exception, should fall back to mock
    res = transcribe_voice("voice_hindi_scn01.ogg", b"MOCK_AUDIO_BYTES")
    assert res["transcript"] != ""
    assert res["source"] in ("MOCK_SARVAM_FALLBACK", "MOCK_FILENAME_MATCH")
    assert "987654321012" in res["transcript"]
