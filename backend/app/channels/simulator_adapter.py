"""In-browser WhatsApp simulator adapter for reliable hackathon demos."""

from typing import Dict, Any
from app.channels.base_adapter import ChannelAdapter


class SimulatorAdapter(ChannelAdapter):
    """Adapter for web UI WhatsApp simulator without external API dependencies."""

    def send_text(self, recipient: str, message: str) -> Dict[str, Any]:
        return {"status": "SUCCESS", "channel": "SIMULATOR", "recipient": recipient, "message": message}

    def send_image(self, recipient: str, image_url: str, caption: str = "") -> Dict[str, Any]:
        return {"status": "SUCCESS", "channel": "SIMULATOR", "recipient": recipient, "image_url": image_url}

    def send_voice(self, recipient: str, audio_url: str) -> Dict[str, Any]:
        return {"status": "SUCCESS", "channel": "SIMULATOR", "recipient": recipient, "audio_url": audio_url}

    def download_media(self, media_id: str) -> bytes:
        return b"SIMULATOR_MOCK_IMAGE_BYTES"

    def handle_incoming_payload(self, raw_payload: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "channel": "SIMULATOR",
            "sender": raw_payload.get("sender", "simulator_user"),
            "text": raw_payload.get("text", ""),
            "media_type": raw_payload.get("media_type"),
        }
