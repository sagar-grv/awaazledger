"""Inbound webhook handlers for WhatsApp channels."""

from fastapi import APIRouter, Request, Depends
from typing import Dict, Any
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.logging import logger
from app.channels.evolution_whatsapp_adapter import EvolutionWhatsAppAdapter
from app.services.channel_message_service import process_text_message
from app.agent.state_machine import AgentOrchestrator

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


@router.post("/whatsapp")
@router.post("/evolution")
async def handle_whatsapp_webhook(
    request: Request,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Inbound webhook processing Evolution API messages with autonomous agent routing."""
    try:
        raw_payload = await request.json()
    except Exception:
        return {"status": "FAILED", "reason": "Invalid JSON body"}

    adapter = EvolutionWhatsAppAdapter()
    normalized = adapter.handle_incoming_payload(raw_payload)

    phone = normalized.get("phone")
    msg_type = normalized.get("message_type")
    text = normalized.get("text")

    if not phone:
        return {"status": "IGNORED", "reason": "No sender phone detected"}

    if msg_type == "text" and text:
        ingest_res = await process_text_message(
            sender_phone=phone,
            user_id=None,
            message=text,
            channel="WHATSAPP_EVOLUTION",
            db=db,
        )

        dispute_id = ingest_res.get("dispute_id")
        reply_text = ingest_res.get("agent_message", "")

        # If dispute created, run autonomous agent and send explanation
        if dispute_id:
            try:
                orchestrator = AgentOrchestrator(db=db)
                agent_res = orchestrator.run_for_dispute(dispute_id)
                reply_text = agent_res.get("explanation_user") or reply_text
            except Exception as e:
                logger.error(f"Autonomous resolution failed during webhook: {str(e)}")

        adapter.send_text(phone, reply_text)
        return {"status": "SUCCESS", "dispute_id": dispute_id, "reply": reply_text}

    elif msg_type in ["voice", "image"]:
        reply_text = (
            "Voice/screenshot webhook received. Media processing will be enabled "
            "when Evolution API media download is configured."
        )
        adapter.send_text(phone, reply_text)
        return {"status": "RECEIVED_MEDIA", "message": reply_text}

    return {"status": "IGNORED", "reason": f"Unhandled message type {msg_type}"}
