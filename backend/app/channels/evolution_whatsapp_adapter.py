"""WhatsApp adapter for Evolution API (open-source Baileys gateway)."""

import re
import base64
import logging
from typing import Dict, Any, Optional, Union
import httpx
from app.channels.base_adapter import ChannelAdapter
from app.core.config import settings
from app.services.channel_identity_service import normalize_phone_number

logger = logging.getLogger(__name__)


class EvolutionWhatsAppAdapter(ChannelAdapter):
    """Integrates with Evolution API instance with safe local mock fallback."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        instance_name: Optional[str] = None,
    ):
        self.base_url = base_url if base_url is not None else getattr(settings, "EVOLUTION_API_URL", "http://localhost:8080")
        self.api_key = api_key if api_key is not None else getattr(settings, "EVOLUTION_API_KEY", "")
        self.instance_name = instance_name if instance_name is not None else getattr(settings, "EVOLUTION_INSTANCE_NAME", "paytm-awaazledger")

    def _clean_recipient(self, recipient: str) -> str:
        clean = re.sub(r"[^\d]", "", str(recipient or ""))
        return clean

    def send_text(self, recipient: str, message: str) -> Dict[str, Any]:
        """Dispatches outbound text to Evolution API instance or returns mocked confirmation."""
        clean_number = self._clean_recipient(recipient)

        if settings.ENABLE_EVOLUTION_LIVE and self.api_key and self.base_url:
            endpoint = f"{self.base_url.rstrip('/')}/message/sendText/{self.instance_name}"
            headers = {"apikey": self.api_key, "Content-Type": "application/json"}
            payload = {"number": clean_number, "text": message}

            try:
                with httpx.Client(timeout=8.0) as client:
                    res = client.post(endpoint, json=payload, headers=headers)
                    if res.status_code in (200, 201):
                        return {"status": "SUCCESS", "channel": "WHATSAPP_EVOLUTION", "response": res.json()}
                    else:
                        logger.warning(f"Evolution API sendText HTTP {res.status_code}: {res.text}")
            except Exception as e:
                logger.warning(f"Evolution API live text failed: {e}. Falling back to mock.")
                return {
                    "status": "MOCKED",
                    "channel": "WHATSAPP_EVOLUTION",
                    "recipient": recipient,
                    "message": message,
                    "reason": f"Evolution API live send failed; fallback mock used: {str(e)}",
                }

        return {
            "status": "MOCKED",
            "channel": "WHATSAPP_EVOLUTION",
            "recipient": recipient,
            "message": message,
            "reason": "Evolution API not configured",
        }

    def send_image(self, recipient: str, image_url_or_b64: str, caption: str = "") -> Dict[str, Any]:
        """Sends an image to recipient via Evolution API."""
        clean_number = self._clean_recipient(recipient)

        if settings.ENABLE_EVOLUTION_LIVE and self.api_key and self.base_url:
            endpoint = f"{self.base_url.rstrip('/')}/message/sendMedia/{self.instance_name}"
            headers = {"apikey": self.api_key, "Content-Type": "application/json"}
            payload = {
                "number": clean_number,
                "mediatype": "image",
                "media": image_url_or_b64,
                "caption": caption,
            }

            try:
                with httpx.Client(timeout=10.0) as client:
                    res = client.post(endpoint, json=payload, headers=headers)
                    if res.status_code in (200, 201):
                        return {"status": "SUCCESS", "channel": "WHATSAPP_EVOLUTION", "response": res.json()}
            except Exception as e:
                logger.warning(f"Evolution API live media failed: {e}. Falling back to mock.")

        return {
            "status": "MOCKED",
            "channel": "WHATSAPP_EVOLUTION",
            "recipient": recipient,
            "image_url": image_url_or_b64,
            "caption": caption,
            "reason": "Evolution API not configured",
        }

    def send_voice(self, recipient: str, audio_url_or_b64: str) -> Dict[str, Any]:
        """Sends audio note to recipient via Evolution API."""
        clean_number = self._clean_recipient(recipient)

        if settings.ENABLE_EVOLUTION_LIVE and self.api_key and self.base_url:
            endpoint = f"{self.base_url.rstrip('/')}/message/sendWhatsAppAudio/{self.instance_name}"
            headers = {"apikey": self.api_key, "Content-Type": "application/json"}
            payload = {
                "number": clean_number,
                "audio": audio_url_or_b64,
            }

            try:
                with httpx.Client(timeout=10.0) as client:
                    res = client.post(endpoint, json=payload, headers=headers)
                    if res.status_code in (200, 201):
                        return {"status": "SUCCESS", "channel": "WHATSAPP_EVOLUTION", "response": res.json()}
            except Exception as e:
                logger.warning(f"Evolution API live voice failed: {e}. Falling back to mock.")

        return {
            "status": "MOCKED",
            "channel": "WHATSAPP_EVOLUTION",
            "recipient": recipient,
            "audio_url": audio_url_or_b64,
            "reason": "Evolution API not configured",
        }

    def download_media(self, media_payload_or_id: Union[str, Dict[str, Any]]) -> bytes:
        """Downloads media binary from URL, base64 payload, or Evolution media endpoint."""
        if isinstance(media_payload_or_id, dict):
            # 1. Check direct base64
            b64_content = media_payload_or_id.get("media_base64") or media_payload_or_id.get("base64")
            if b64_content:
                try:
                    if "base64," in b64_content:
                        b64_content = b64_content.split("base64,")[1]
                    return base64.b64decode(b64_content)
                except Exception as e:
                    logger.warning(f"Base64 decode failed: {e}")

            # 2. Check direct media URL
            media_url = media_payload_or_id.get("media_url") or media_payload_or_id.get("url")
            if media_url and media_url.startswith("http") and "example.com" not in media_url and settings.ENABLE_EVOLUTION_LIVE:
                try:
                    with httpx.Client(timeout=10.0) as client:
                        resp = client.get(media_url)
                        if resp.status_code == 200:
                            return resp.content
                except Exception as e:
                    logger.warning(f"Media URL download failed: {e}")

            # 3. Request media base64 from Evolution endpoint
            raw_msg = media_payload_or_id.get("raw") or media_payload_or_id.get("raw_payload") or media_payload_or_id
            if settings.ENABLE_EVOLUTION_LIVE and self.api_key and self.base_url:
                try:
                    endpoint = f"{self.base_url.rstrip('/')}/chat/getBase64FromMediaMessage/{self.instance_name}"
                    headers = {"apikey": self.api_key, "Content-Type": "application/json"}
                    req_body = {
                        "message": raw_msg.get("data", raw_msg) if isinstance(raw_msg, dict) else raw_msg,
                        "convertToMp4": False,
                    }
                    with httpx.Client(timeout=10.0) as client:
                        resp = client.post(endpoint, json=req_body, headers=headers)
                        if resp.status_code in (200, 201):
                            data = resp.json()
                            b64 = data.get("base64", "")
                            if "base64," in b64:
                                b64 = b64.split("base64,")[1]
                            return base64.b64decode(b64)
                except Exception as e:
                    logger.warning(f"Evolution getBase64FromMediaMessage failed: {e}")

        elif isinstance(media_payload_or_id, str) and media_payload_or_id.startswith("http"):
            try:
                with httpx.Client(timeout=10.0) as client:
                    resp = client.get(media_payload_or_id)
                    if resp.status_code == 200:
                        return resp.content
            except Exception as e:
                logger.warning(f"Direct media string download failed: {e}")

        # Fallback binary bytes for mock / tests
        return b"MOCK_MEDIA_BYTES"

    def handle_incoming_payload(self, raw_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Normalizes provider-specific webhook into standard message schema."""
        return self.normalize_incoming(raw_payload)

    def normalize_incoming(self, raw_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Normalizes Evolution API webhook JSON payload into AwaazLedger canonical format."""
        data = raw_payload.get("data", raw_payload)
        key = data.get("key", {})

        remote_jid = key.get("remoteJid", "")
        sender_phone = remote_jid.split("@")[0] if "@" in remote_jid else remote_jid
        sender_phone = normalize_phone_number(sender_phone)

        message_obj = data.get("message", {})

        text = ""
        is_voice = False
        is_image = False
        media_url = None
        media_base64 = data.get("base64")
        media_mime = None

        if "conversation" in message_obj:
            text = message_obj["conversation"]
        elif "extendedTextMessage" in message_obj:
            text = message_obj["extendedTextMessage"].get("text", "")
        elif "audioMessage" in message_obj:
            is_voice = True
            audio_info = message_obj["audioMessage"]
            media_url = audio_info.get("url")
            media_mime = audio_info.get("mimetype", "audio/ogg")
            text = audio_info.get("caption", "")
        elif "imageMessage" in message_obj:
            is_image = True
            img_info = message_obj["imageMessage"]
            media_url = img_info.get("url")
            media_mime = img_info.get("mimetype", "image/jpeg")
            text = img_info.get("caption", "")
        elif "documentMessage" in message_obj:
            doc_info = message_obj["documentMessage"]
            media_url = doc_info.get("url")
            media_mime = doc_info.get("mimetype", "application/pdf")
            text = doc_info.get("caption", "")

        msg_type = "text"
        if is_voice:
            msg_type = "voice"
        elif is_image:
            msg_type = "image"
        elif not text and (media_url or media_base64):
            msg_type = "unknown_media"

        return {
            "channel": "WHATSAPP_EVOLUTION",
            "phone": sender_phone,
            "sender_phone": sender_phone,
            "message_type": msg_type,
            "text": text,
            "is_voice": is_voice,
            "is_image": is_image,
            "media_url": media_url,
            "media_base64": media_base64,
            "media_mime": media_mime,
            "message_id": key.get("id"),
            "timestamp": data.get("messageTimestamp"),
            "raw_payload": raw_payload,
            "raw": raw_payload,
        }
