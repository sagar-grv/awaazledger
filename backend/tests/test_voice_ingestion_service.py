"""Unit tests for voice note transcription and entity resolution."""

from app.services.voice_ingestion_service import transcribe_voice


def test_voice_ingestion_known_scenario():
    filename = "voice_hindi_scn01.ogg"
    content = b"MOCK_OGG_BYTES"
    res = transcribe_voice(filename, content)

    assert "987654321012" in res["transcript"]
    assert res["language"] == "hi"
    assert res["entities"].utr == "987654321012"
    assert res["entities"].amount == 450.0
    assert res["source"] == "MOCK_SARVAM_FALLBACK"


def test_voice_ingestion_unknown_fallback():
    filename = "random_recording.ogg"
    content = b"UNKNOWN_BYTES"
    res = transcribe_voice(filename, content)

    assert "No UTR provided" in res["transcript"]
    assert res["entities"].utr is None
    assert "utr" in res["entities"].missing_fields
