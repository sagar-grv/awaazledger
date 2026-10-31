"""Voice note ingestion service supporting Sarvam AI Speech-to-Text and deterministic hackathon mock fallbacks."""

import os
import json
import logging
from typing import Dict, Any, Optional
from app.core.config import settings
from app.services.intent_extractor import extract_entities_from_text

logger = logging.getLogger(__name__)

_VOICE_DATA_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "mock_voice_transcripts.json")
)


class AwaitableDict(dict):
    """Dictionary that can be used directly or awaited in async contexts."""

    def __await__(self):
        async def _coro():
            return self
        return _coro().__await__()


def _try_real_sarvam_stt(filename: str, content: bytes) -> Optional[Dict[str, Any]]:
    """Attempts real transcription using Sarvam AI STT API if configured; returns None on any failure."""
    if not (settings.ENABLE_SARVAM_REAL and settings.SARVAM_API_KEY and settings.SARVAM_STT_ENDPOINT):
        return None

    try:
        import httpx

        headers = {
            "api-subscription-key": settings.SARVAM_API_KEY,
        }
        files = {
            "file": (filename or "audio.wav", content, "audio/wav"),
        }
        data = {
            "model": "saarika:v1",
            "language_code": "hi-IN",
        }

        with httpx.Client(timeout=10.0) as client:
            resp = client.post(settings.SARVAM_STT_ENDPOINT, headers=headers, files=files, data=data)
            if resp.status_code == 200:
                body = resp.json()
                text = (
                    body.get("transcript")
                    or body.get("text")
                    or body.get("result")
                    or (body.get("data") or {}).get("text")
                    or ""
                )
                if text:
                    language = body.get("language_code", "hi")[:2]
                    entities = extract_entities_from_text(text, default_language=language)
                    return {
                        "transcript": text,
                        "language": language,
                        "entities": entities,
                        "source": "SARVAM_AI_LIVE",
                    }
    except Exception as e:
        logger.warning(f"Real Sarvam STT failed: {e}. Falling back to deterministic mock.")

    return None


def transcribe_voice(
    filename: str,
    content: bytes,
    default_language: Optional[str] = None,
) -> AwaitableDict:
    """Transcribes audio payload to vernacular transcript and extracts structured entities."""
    # 1. Attempt optional live Sarvam STT if enabled
    real_result = _try_real_sarvam_stt(filename, content)
    if real_result:
        return AwaitableDict(real_result)

    # 2. Deterministic mock fallback
    filename_lower = (filename or "").lower()

    transcripts_map = {}
    if os.path.exists(_VOICE_DATA_PATH):
        try:
            with open(_VOICE_DATA_PATH, "r", encoding="utf-8") as f:
                transcripts_map = json.load(f)
        except Exception:
            transcripts_map = {}

    matched_entry = None
    for key, val in transcripts_map.items():
        if key.lower() in filename_lower:
            matched_entry = val
            break

    if matched_entry:
        transcript = matched_entry.get("transcript", "")
        language = matched_entry.get("language") or default_language or "hi"
    else:
        transcript = "User reported pending UPI payment. No UTR provided."
        language = default_language or "hi"

    source = "MOCK_SARVAM_FALLBACK"

    entities = extract_entities_from_text(transcript, default_language=language)

    return AwaitableDict({
        "transcript": transcript,
        "language": language,
        "entities": entities,
        "source": source,
    })
