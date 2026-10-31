"""Sarvam AI Text-to-Speech client stub."""

from typing import Dict, Any, Optional
from app.core.config import settings


class SarvamTTSClient:
    """Client for Sarvam AI Bulbul text-to-speech API."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.SARVAM_API_KEY

    def synthesize(self, text: str, language_code: str = "hi-IN") -> Dict[str, Any]:
        """Synthesizes vernacular audio response."""
        return {
            "audio_url": "https://assets.awaazledger.local/mock_response.wav",
            "duration_seconds": 3.8,
            "format": "wav",
        }
