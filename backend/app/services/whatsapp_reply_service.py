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
        if lang in ("hi", "mr", "hinglish"):
            msg = (
                f"Namaste 🙏 Main AwaazLedger hoon.\n\n"
                f"Aapki complaint mil gayi hai (Ref: *{dispute_code}*).\n"
                f"Main Core Banking (CBS), NPCI switch, aur Paytm ledger se verify kar raha hoon. Kripya thoda intezaar karein..."
            )
        else:
            msg = (
                f"Hello 🙏 I am AwaazLedger.\n\n"
                f"I received your dispute request (Ref: *{dispute_code}*).\n"
                f"I am actively verifying across Core Banking, NPCI, and Paytm ledgers. Please hold on..."
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

        # 1. Decision Header Badge
        if decision in ("AUTO_RESOLVE", "AUTO_BRIDGE_CREDIT"):
            badge = "✅ *PROVISIONAL BRIDGE CREDIT PROVIDED*"
        elif decision in ("HUMAN_ESCALATE", "ESCALATED"):
            badge = "👥 *ROUTED TO SENIOR OPERATIONS SPECIALIST*"
        elif decision in ("FRAUD_BLOCK", "MANUALLY_BLOCKED_FRAUD"):
            badge = "🛡️ *RISK VERIFICATION LOCK APPLIED*"
        elif decision in ("GHOST_SUCCESS_RECEIPT", "RECEIPT_GENERATED"):
            badge = "🧾 *VERIFIED DIGITAL MERCHANT RECEIPT GENERATED*"
        else:
            badge = "ℹ️ *DISPUTE INVESTIGATION UPDATE*"

        # 2. Multi-Node Status Checkpoints
        nodes_text = (
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "*Financial Truth Trace:*\n"
            "• Remitter Bank: ✅ Debited\n"
            "• NPCI Switch: ⏳ Delayed / In-Transit\n"
            "• Beneficiary Bank: ❌ Not Credited\n"
            "• Paytm Settlement: ⏳ Pending\n"
            "• Bridge Credit: " + ("✅ Provided\n" if "AUTO" in decision else "⏳ Pending\n") +
            "• RBI TAT Timer: ⏳ Active (T+1 Rule)\n"
            "━━━━━━━━━━━━━━━━━━━━━"
        )

        user_exp = dispute.explanation_user or "Aapka dispute process kar diya gaya hai."

        # 3. Optional Public Tracker Link
        tracker_link = ""
        public_url = getattr(settings, "PUBLIC_APP_URL", "")
        if public_url:
            tracker_link = f"\n\n🔍 Live Tracker Link:\n{public_url}/tracker?code={code}"

        full_message = (
            f"{badge}\n\n"
            f"Reference: *{code}*\n"
            f"Claimed Amount: *{amount_str}*\n\n"
            f"{user_exp}\n\n"
            f"{nodes_text}"
            f"{tracker_link}\n\n"
            f"_AwaazLedger Autonomous AI Teammate for Paytm UPI_"
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
        if lang in ("hi", "mr", "hinglish"):
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
