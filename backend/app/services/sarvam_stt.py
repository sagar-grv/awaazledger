"""Sarvam AI Speech-to-Text client stub."""

from typing import Dict, Any, Optional
from app.core.config import settings


class SarvamSTTClient:
    """Client for Sarvam AI Saaras speech-to-text API."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.SARVAM_API_KEY

    def transcribe(self, audio_bytes: bytes, language_code: str = "hi-IN") -> Dict[str, Any]:
        """Transcribes incoming voice note to text with confidence."""
        # Placeholder mock for hackathon prototype
        return {
            "transcript": "Mera 500 rupaye kat gaya par dukaan pe payment nahi hua. UTR 987654321012.",
            "language_code": language_code,
            "confidence": 0.94,
        }
