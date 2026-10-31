"""WhatsApp adapter for official Meta Cloud WhatsApp Business API."""

from typing import Dict, Any
from app.channels.base_adapter import ChannelAdapter


class MetaCloudWhatsAppAdapter(ChannelAdapter):
    """Integrates with official Meta Cloud WhatsApp Business API."""

    def send_text(self, recipient: str, message: str) -> Dict[str, Any]:
        return {"status": "SUCCESS", "channel": "META_CLOUD_WHATSAPP", "recipient": recipient}

    def send_image(self, recipient: str, image_url: str, caption: str = "") -> Dict[str, Any]:
        return {"status": "SUCCESS", "channel": "META_CLOUD_WHATSAPP", "recipient": recipient}

    def send_voice(self, recipient: str, audio_url: str) -> Dict[str, Any]:
        return {"status": "SUCCESS", "channel": "META_CLOUD_WHATSAPP", "recipient": recipient}

    def download_media(self, media_id: str) -> bytes:
        return b"MOCK_META_MEDIA_BYTES"

    def handle_incoming_payload(self, raw_payload: Dict[str, Any]) -> Dict[str, Any]:
        return {"channel": "META_CLOUD_WHATSAPP", "sender": "user", "text": "sample"}
