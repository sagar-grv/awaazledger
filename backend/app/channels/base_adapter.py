"""Base adapter interface for messaging channels."""

from abc import ABC, abstractmethod
from typing import Dict, Any


class ChannelAdapter(ABC):
    """Abstract base class for all conversational channel adapters."""

    @abstractmethod
    def send_text(self, recipient: str, message: str) -> Dict[str, Any]:
        """Sends a text message to recipient."""
        pass

    @abstractmethod
    def send_image(self, recipient: str, image_url: str, caption: str = "") -> Dict[str, Any]:
        """Sends an image to recipient."""
        pass

    @abstractmethod
    def send_voice(self, recipient: str, audio_url: str) -> Dict[str, Any]:
        """Sends a voice message to recipient."""
        pass

    @abstractmethod
    def download_media(self, media_id: str) -> bytes:
        """Downloads media binary from channel provider."""
        pass

    @abstractmethod
    def handle_incoming_payload(self, raw_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Normalizes provider-specific webhook into standard message schema."""
        pass
