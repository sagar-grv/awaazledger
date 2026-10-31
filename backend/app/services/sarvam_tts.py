"""Sarvam AI Text-to-Speech (TTS) integration for vernacular voice responses."""

import os
import logging
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


class SarvamTTSClient:
    """Client for generating vernacular voice notes via Sarvam AI TTS API."""

    def __init__(self):
        self.api_key = settings.SARVAM_API_KEY
        self.endpoint = settings.SARVAM_TTS_ENDPOINT

    def generate_voice(self, text: str, dispute_code: str, language: str = "hi") -> Optional[str]:
        return generate_voice_reply(text, dispute_code, language)


def generate_voice_reply(text: str, dispute_code: str, language: str = "hi") -> Optional[str]:
    """Converts user explanation text to voice audio file via Sarvam AI TTS API."""
    sarvam_enabled = getattr(settings, "ENABLE_SARVAM_REAL", False) or getattr(settings, "ENABLE_WHATSAPP_VOICE_REPLY", False)
    if not (sarvam_enabled and settings.SARVAM_API_KEY and settings.SARVAM_TTS_ENDPOINT):
        return None

    try:
        import httpx

        # Map language code to Sarvam supported target language
        target_lang = "hi-IN"
        if language == "mr":
            target_lang = "mr-IN"
        elif language == "ta":
            target_lang = "ta-IN"
        elif language == "te":
            target_lang = "te-IN"
        elif language == "bn":
            target_lang = "bn-IN"
        elif language == "en":
            target_lang = "en-IN"

        payload = {
            "inputs": [text[:500]],  # Truncate to avoid oversized TTS requests
            "target_language_code": target_lang,
            "speaker": "meera",
            "model": "bulbul:v1",
        }

        headers = {
            "api-subscription-key": settings.SARVAM_API_KEY,
            "Content-Type": "application/json",
        }

        with httpx.Client(timeout=10.0) as client:
            resp = client.post(settings.SARVAM_TTS_ENDPOINT, json=payload, headers=headers)
            if resp.status_code == 200:
                body = resp.json()
                audios = body.get("audios") or body.get("audio") or []
                if audios:
                    b64_audio = audios[0] if isinstance(audios, list) else audios
                    # Save to local cache dir
                    tts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "tmp", "tts"))
                    os.makedirs(tts_dir, exist_ok=True)
                    out_path = os.path.join(tts_dir, f"{dispute_code}.mp3")

                    import base64
                    with open(out_path, "wb") as f:
                        f.write(base64.b64decode(b64_audio))

                    logger.info(f"Generated Sarvam TTS audio: {out_path}")
                    return out_path
    except Exception as e:
        logger.warning(f"Sarvam AI TTS generation failed: {e}. Falling back to text response only.")

    return None
