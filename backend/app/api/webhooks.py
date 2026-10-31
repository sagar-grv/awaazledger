"""Inbound webhook handlers for WhatsApp Evolution API and automated agent routing."""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.config import settings
from app.models.dispute import Dispute
from app.models.processed_message import ProcessedMessage
from app.channels.evolution_whatsapp_adapter import EvolutionWhatsAppAdapter
from app.services.channel_message_service import (
    process_text_message,
    process_voice_message,
    process_image_message,
)
from app.agent.state_machine import AgentOrchestrator
from app.services.whatsapp_reply_service import WhatsAppReplyService
from app.services.feedback_service import FeedbackService, hash_phone
from app.services.learning_service import AgentLearningService
from app.services.sarvam_tts import generate_voice_reply
from app.services.tracker_image_service import generate_tracker_image
from app.api.disputes import _build_tracker_response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


@router.get("/whatsapp/health")
def get_whatsapp_webhook_health():
    """Returns Evolution API webhook status and real-mode feature flag diagnostics."""
    return {
        "status": "HEALTHY",
        "whatsapp_mode": getattr(settings, "WHATSAPP_MODE", "simulator"),
        "evolution_live": getattr(settings, "ENABLE_EVOLUTION_LIVE", False),
        "evolution_api_url": getattr(settings, "EVOLUTION_API_URL", "http://localhost:8080"),
        "instance_name": getattr(settings, "EVOLUTION_INSTANCE_NAME", "paytm-awaazledger"),
        "sarvam_real": getattr(settings, "ENABLE_SARVAM_REAL", False),
        "ocr_real": getattr(settings, "ENABLE_OCR_REAL", False),
        "feedback_enabled": getattr(settings, "FEEDBACK_ENABLED", True),
    }


def process_whatsapp_payload(raw_payload: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """Synchronous core engine for processing incoming Evolution WhatsApp payloads."""
    adapter = EvolutionWhatsAppAdapter()
    normalized = adapter.handle_incoming_payload(raw_payload)

    message_id = normalized.get("message_id")
    phone = normalized.get("phone")
    msg_type = normalized.get("message_type")
    text = (normalized.get("text") or "").strip()

    # 1. Message Idempotency Check
    if message_id:
        existing = db.query(ProcessedMessage).filter(ProcessedMessage.message_id == message_id).first()
        if existing:
            return {"status": "DUPLICATE", "message_id": message_id}

        proc = ProcessedMessage(
            channel="WHATSAPP_EVOLUTION",
            message_id=message_id,
            phone_hash=hash_phone(phone) if phone else None,
            status="PROCESSED",
        )
        db.add(proc)
        db.commit()

    if not phone:
        return {"status": "IGNORED", "reason": "No sender phone detected"}

    reply_svc = WhatsAppReplyService()
    feedback_svc = FeedbackService(db)

    # 2. Check for Pending Feedback Response
    is_feedback_rating = feedback_svc.parse_whatsapp_feedback(text) is not None
    if msg_type == "text" and text and (feedback_svc.has_pending_feedback(phone) or is_feedback_rating):
        consumed_fb = feedback_svc.consume_feedback(phone, text)
        if consumed_fb:
            rating = consumed_fb.rating
            if rating == "HELPFUL":
                thank_you = "Shukriya 🙏 Aapka feedback note kar liya gaya hai."
            elif rating == "NOT_HELPFUL":
                thank_you = "Shukriya. Main aapka case human supervisor desk ko escalate kar raha hoon."
            elif rating == "HUMAN_REQUEST":
                thank_you = "Aapka request supervisor desk ko bhej diya gaya hai. Kripya intezaar karein."
            elif rating == "WRONG_DECISION":
                thank_you = "Feedback received. Case ko quality review escalation queue me daal diya gaya hai."
            else:
                thank_you = "Shukriya! Aapka feedback record ho gaya hai."

            adapter.send_text(phone, thank_you)

            # Record feedback to self-improvement learning engine
            try:
                disp_obj = db.query(Dispute).filter(Dispute.id == consumed_fb.dispute_id).first() if consumed_fb.dispute_id else None
                learning_svc = AgentLearningService(db)
                learning_svc.record_feedback_learning(disp_obj, rating, raw_text=text, phone=phone)
            except Exception as e:
                logger.warning(f"Failed to record feedback learning: {e}")

            return {
                "status": "FEEDBACK_PROCESSED",
                "phone": phone,
                "rating": rating,
                "feedback_id": consumed_fb.id,
            }

    # 3. Route Incoming Message by Modality
    ingest_res = None
    if msg_type == "text" and text:
        ingest_res = process_text_message(
            sender_phone=phone,
            user_id=None,
            message=text,
            channel="WHATSAPP_EVOLUTION",
            db=db,
        )
    elif msg_type == "voice":
        media_bytes = adapter.download_media(normalized)
        voice_fn = "voice_note.ogg"
        if text and ("." in text or "voice" in text or "ogg" in text):
            voice_fn = text
        elif normalized.get("media_url"):
            voice_fn = normalized["media_url"].split("/")[-1].split("?")[0] or "voice_note.ogg"

        ingest_res = process_voice_message(
            sender_phone=phone,
            user_id=None,
            filename=voice_fn,
            content=media_bytes,
            channel="WHATSAPP_EVOLUTION",
            db=db,
        )
    elif msg_type == "image":
        media_bytes = adapter.download_media(normalized)
        img_fn = "receipt.jpg"
        if text and ("." in text or "screenshot" in text or "jpg" in text):
            img_fn = text
        elif normalized.get("media_url"):
            img_fn = normalized["media_url"].split("/")[-1].split("?")[0] or "receipt.jpg"

        ingest_res = process_image_message(
            sender_phone=phone,
            user_id=None,
            filename=img_fn,
            content=media_bytes,
            channel="WHATSAPP_EVOLUTION",
            db=db,
        )
    else:
        return {"status": "IGNORED", "reason": f"Unhandled message type: {msg_type}"}

    dispute_id = ingest_res.get("dispute_id")
    dispute_code = ingest_res.get("dispute_code")
    agent_message = ingest_res.get("agent_message", "")

    # 4. If missing UTR or unknown phone, reply prompt
    if ingest_res.get("needs_more_info") or not dispute_id:
        adapter.send_text(phone, agent_message)
        if msg_type == "voice":
            try:
                prompt_lang = ingest_res.get("entities", {}).language if hasattr(ingest_res.get("entities"), "language") else "hi"
                voice_fn = generate_voice_reply(agent_message, "PROMPT", language=prompt_lang)
                if voice_fn:
                    adapter.send_voice(phone, voice_fn)
            except Exception as e:
                logger.warning(f"Voice prompt generation error: {e}")

        return {
            "status": "NEEDS_INFO",
            "phone": phone,
            "agent_message": agent_message,
        }

    # 5. Send Immediate Acknowledgment
    lang = ingest_res.get("entities", {}).language if hasattr(ingest_res.get("entities"), "language") else "hi"
    reply_svc.send_agent_ack(phone, lang, dispute_code)

    # 6. Execute Autonomous Agent Orchestration Loop
    try:
        orchestrator = AgentOrchestrator(db=db)
        agent_res = orchestrator.run_for_dispute(dispute_id)
    except Exception as e:
        logger.error(f"Autonomous agent execution error in webhook: {e}")
        reply_svc.send_error_message(phone, lang)
        return {"status": "AGENT_ERROR", "error": str(e)}

    # 7. Fetch Updated Dispute & Multi-Node Tracker
    disp = db.query(Dispute).filter(Dispute.id == dispute_id).first()
    if not disp:
        return {"status": "ERROR", "reason": "Dispute not found after agent run"}

    tracker = _build_tracker_response(disp, db)

    # 8. Send Formatted WhatsApp Result Message (+ optional TTS/image)
    reply_svc.send_agent_result(phone, disp, tracker, language=disp.language)

    # Ensure voice note reply if user sent a voice note
    if msg_type == "voice":
        try:
            voice_path = generate_voice_reply(disp.explanation_user or "Dispute verified and resolved.", disp.dispute_code, language=disp.language)
            if voice_path:
                adapter.send_voice(phone, voice_path)
        except Exception as e:
            logger.warning(f"Voice note reply dispatch failed: {e}")

    # Ensure status card image if user uploaded screenshot
    if msg_type == "image":
        try:
            img_path = generate_tracker_image(disp.dispute_code, tracker)
            if img_path:
                adapter.send_image(phone, img_path, caption=f"Dispute Status Card: {disp.dispute_code}")
        except Exception as e:
            logger.warning(f"Status card image dispatch failed: {e}")

    # Record autonomous settlement in continuous learning engine
    try:
        learning_svc = AgentLearningService(db)
        learning_svc.record_autonomous_resolution(disp, modality=msg_type.upper())
    except Exception as e:
        logger.warning(f"Failed to record autonomous resolution learning: {e}")

    # 9. Register & Send Feedback Prompt
    if getattr(settings, "FEEDBACK_ENABLED", True):
        feedback_svc.register_pending_feedback(phone, disp.id)
        reply_svc.send_feedback_prompt(phone, disp.id, language=disp.language)

    return {
        "status": "SUCCESS",
        "dispute_id": disp.id,
        "dispute_code": disp.dispute_code,
        "decision": disp.agent_decision,
        "risk_level": disp.risk_level,
        "phone": phone,
    }


@router.post("/whatsapp")
@router.post("/evolution")
async def handle_whatsapp_webhook(
    request: Request,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Inbound webhook processing Evolution API messages with autonomous agent routing and feedback."""
    try:
        raw_payload = await request.json()
    except Exception:
        return {"status": "FAILED", "reason": "Invalid JSON body"}

    return process_whatsapp_payload(raw_payload, db)
