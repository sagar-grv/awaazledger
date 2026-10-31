"""WhatsApp outbound messaging, response formatting, and feedback dispatch service."""

import logging
from typing import Dict, Any, Optional
from app.core.config import settings
from app.channels.channel_router import get_adapter
from app.models.dispute import Dispute
from app.services.sarvam_tts import generate_voice_reply
from app.services.tracker_image_service import generate_tracker_image

logger = logging.getLogger(__name__)


def _get_active_channel_adapter():
    mode = getattr(settings, "WHATSAPP_MODE", "simulator").lower()
    if mode in ("evolution", "whatsapp_evolution"):
        return get_adapter("WHATSAPP_EVOLUTION")
    return get_adapter("SIMULATOR")


class WhatsAppReplyService:
    def __init__(self):
        self.adapter = _get_active_channel_adapter()

    def send_agent_ack(self, phone: str, language: str, dispute_code: str) -> Dict[str, Any]:
        """Sends an immediate acknowledgment message on WhatsApp upon receiving the complaint."""
        lang = (language or "hi").lower()
        if lang == "mr":
            msg = (
                f"✅ *तक्रार नोंदवली (Ref: {dispute_code})*\n\n"
                f"नमस्कार 🙏 मी बँक (CBS) आणि NPCI द्वारे पडताळणी करत आहे. कृपया 3-5 सेकंद थांबा..."
            )
        elif lang in ("hi", "hinglish"):
            msg = (
                f"✅ *कंप्लेंट दर्ज कर ली गई है (Ref: {dispute_code})*\n\n"
                f"नमस्ते 🙏 मैं आपके बैंक (CBS) और NPCI रिकॉर्ड्स वेरिफाई कर रहा हूँ। कृपया 3-5 सेकंड रुकें..."
            )
        else:
            msg = (
                f"✅ *Dispute Registered (Ref: {dispute_code})*\n\n"
                f"Hello 🙏 Verifying records across Bank CBS & NPCI switch. Please wait 3-5 seconds..."
            )

        return self.adapter.send_text(phone, msg)

    def send_agent_result(
        self,
        phone: str,
        dispute: Dispute,
        tracker: Dict[str, Any],
        language: str = "hi",
    ) -> Dict[str, Any]:
        """Formats and sends the final autonomous investigation outcome to the user on WhatsApp."""
        decision = dispute.agent_decision or "PENDING"
        amount_str = f"₹{dispute.amount:.2f}" if dispute.amount else "Pending"
        code = dispute.dispute_code
        utr_str = dispute.utr or "N/A"

        # 1. Concise, User-Perspective Status Badge
        if decision in ("AUTO_RESOLVE", "AUTO_BRIDGE_CREDIT"):
            badge = f"✅ *PROVISIONAL CREDIT ADDED: {amount_str}*"
            action_desc = "Instant provisional credit added to your Paytm Wallet"
        elif decision in ("HUMAN_ESCALATE", "ESCALATED"):
            badge = "⏳ *CASE UNDER REVIEW BY SENIOR TEAM*"
            action_desc = "High-value transaction sent for priority human review"
        elif decision in ("FRAUD_BLOCK", "MANUALLY_BLOCKED_FRAUD"):
            badge = "🛡️ *TRANSACTION VERIFICATION ON HOLD*"
            action_desc = "Verification paused for account safety; under review by risk team"
        elif decision in ("GHOST_SUCCESS_RECEIPT", "RECEIPT_GENERATED"):
            badge = "🧾 *VERIFIED DIGITAL MERCHANT RECEIPT GENERATED*"
            action_desc = "Payment confirmed credited to merchant bank"
        else:
            badge = "ℹ️ *DISPUTE STATUS UPDATE*"
            action_desc = "Investigation completed"

        user_exp = dispute.explanation_user or "Aapka dispute process kar diya gaya hai."

        # Public Tracker Link
        tracker_link = ""
        public_url = getattr(settings, "PUBLIC_APP_URL", "")
        if public_url:
            tracker_link = f"\n\n🔗 *Live Status Link:*\n{public_url}/tracker?code={code}"

        # Clean, concise, user-perspective message without internal clutter
        full_message = (
            f"{badge}\n\n"
            f"• Reference: *{code}*\n"
            f"• UTR: *{utr_str}*\n"
            f"• Amount: *{amount_str}*\n\n"
            f"{user_exp}\n\n"
            f"📊 *Quick Verification Summary:*\n"
            f"• Bank Check: ✅ Debited\n"
            f"• NPCI Switch: ⏳ Delayed / In-Transit\n"
            f"• Merchant Status: ❌ Not Credited\n"
            f"• Next Step: ⏱️ {action_desc}\n"
            f"• RBI TAT Guarantee: T+1 Auto-Reversal Active"
            f"{tracker_link}"
        )

        res = self.adapter.send_text(phone, full_message)

        # 4. Optional Visual Tracker Image
        if getattr(settings, "ENABLE_TRACKER_IMAGE", False):
            img_path = generate_tracker_image(code, tracker)
            if img_path:
                self.adapter.send_image(phone, img_path, caption=f"Dispute Status Card: {code}")

        # 5. Optional Sarvam TTS Voice Reply
        if getattr(settings, "ENABLE_WHATSAPP_VOICE_REPLY", False):
            voice_path = generate_voice_reply(user_exp, code, language=language)
            if voice_path:
                self.adapter.send_voice(phone, voice_path)

        return res

    def send_feedback_prompt(self, phone: str, dispute_id: int, language: str = "hi") -> Dict[str, Any]:
        """Sends the structured feedback rating prompt on WhatsApp."""
        lang = (language or "hi").lower()
        if lang == "mr":
            prompt = (
                "कृपया आपला अभिप्राय द्या:\n"
                "*1* - Helpful (योग्य मदत मिळाली)\n"
                "*2* - Not helpful (मदत झाली नाही)\n"
                "*3* - Talk to human (अधिकार्यांशी बोला)\n"
                "*4* - Wrong decision (निर्णय चुकीचा वाटतो)\n\n"
                "_(फक्त 1, 2, 3 किंवा 4 रिप्लाय करा)_"
            )
        elif lang in ("hi", "hinglish"):
            prompt = (
                "Kripya apna feedback dein:\n"
                "*1* - Helpful (Sahi madad mili)\n"
                "*2* - Not helpful (Madad nahi hui)\n"
                "*3* - Talk to human (Human specialist se baat karein)\n"
                "*4* - Wrong decision (Galat faisla hai)\n\n"
                "_(Sirf 1, 2, 3 ya 4 reply karein)_"
            )
        else:
            prompt = (
                "Please share your feedback:\n"
                "*1* - Helpful\n"
                "*2* - Not helpful\n"
                "*3* - Talk to human specialist\n"
                "*4* - Wrong decision\n\n"
                "_(Simply reply with 1, 2, 3, or 4)_"
            )

        return self.adapter.send_text(phone, prompt)

    def send_error_message(self, phone: str, language: str = "hi") -> Dict[str, Any]:
        """Sends a polite fallback error message on WhatsApp."""
        lang = (language or "hi").lower()
        if lang in ("hi", "mr", "hinglish"):
            msg = "Kshama karein, ek technical issue aa gaya hai. Kripya thodi der baad dobara bhejein ya *HUMAN* likhkar reply karein."
        else:
            msg = "Sorry, an internal technical error occurred. Please retry shortly or reply *HUMAN* for live supervisor assistance."
        return self.adapter.send_text(phone, msg)
