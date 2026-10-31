"""Unified channel message orchestrator connecting text, voice, and OCR to dispute registration."""

from uuid import uuid4
import json
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.dispute import Dispute
from app.models.user import User
from app.models.transaction import Transaction
from app.schemas.dispute import DisputeStatus, AgentDecision
from app.schemas.ingest import ExtractedEntity, IntentType
from app.services.channel_identity_service import resolve_user_by_phone
from app.services.intent_extractor import extract_entities_from_text
from app.services.voice_ingestion_service import transcribe_voice
from app.services.ocr_service import extract_ocr_from_image


class AwaitableDict(dict):
    """Dictionary that can be used directly or awaited in async contexts."""

    def __await__(self):
        async def _coro():
            return self
        return _coro().__await__()


def _resolve_user_id(db: Session, sender_phone: Optional[str], user_id: Optional[int]) -> Optional[Dict[str, Any]]:
    """Resolves active user record and metadata by ID or phone."""
    if user_id:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            return {"user_id": user.id, "language": user.language or "hi", "name": user.name}

    if sender_phone:
        resolved = resolve_user_by_phone(sender_phone)
        if resolved:
            return resolved

    return None


def process_text_message(
    sender_phone: Optional[str],
    user_id: Optional[int],
    message: str,
    channel: str = "SIMULATOR",
    db: Optional[Session] = None,
) -> AwaitableDict:
    """Ingests text message, extracts intent/entities, and initiates dispute if UTR is detected."""
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    try:
        user_info = _resolve_user_id(db, sender_phone, user_id)
        if not user_info:
            return AwaitableDict({
                "channel": channel,
                "user_id": None,
                "dispute_id": None,
                "dispute_code": None,
                "needs_more_info": True,
                "agent_message": "This number is not registered for the demo. Please select a demo user or use a registered WhatsApp number.",
                "entities": ExtractedEntity(raw_text=message),
                "transcript": message,
                "ocr_json": None,
            })

        uid = user_info["user_id"]
        lang = user_info.get("language", "hi")
        entities = extract_entities_from_text(message, default_language=lang)

        # Require UTR to initiate formal dispute
        if not entities.utr:
            prompt = (
                "Mujhe 12-digit UTR ya bank debit screenshot chahiye taaki main transaction verify kar sakun."
                if lang in ["hi", "mr"]
                else "Please share the 12-digit UTR or upload a bank debit screenshot so I can verify the transaction."
            )
            return AwaitableDict({
                "channel": channel,
                "user_id": uid,
                "dispute_id": None,
                "dispute_code": None,
                "needs_more_info": True,
                "agent_message": prompt,
                "entities": entities,
                "transcript": message,
                "ocr_json": None,
            })

        # Query transaction
        txn = db.query(Transaction).filter(Transaction.utr == entities.utr).first()
        claimed_amount = entities.amount if entities.amount is not None else (txn.amount if txn else None)
        amount = claimed_amount if claimed_amount is not None else (txn.amount if txn else 0.0)

        dispute_code = f"DISP-{uuid4().hex[:8].upper()}"
        intent_val = entities.intent.value if hasattr(entities.intent, "value") else str(entities.intent)
        dispute = Dispute(
            dispute_code=dispute_code,
            user_id=uid,
            transaction_id=txn.id if txn else None,
            utr=entities.utr,
            claimed_amount=claimed_amount,
            amount=amount,
            channel=channel,
            intent=intent_val,
            language=entities.language or lang,
            transcript=message,
            status=DisputeStatus.PENDING.value,
            agent_decision=AgentDecision.PENDING_ANALYSIS.value,
            identity_verified=False,
        )
        db.add(dispute)
        db.commit()
        db.refresh(dispute)

        agent_msg = (
            f"Dispute {dispute_code} register ho gaya hai. Main CBS, NPCI aur Paytm ledger se verify kar raha hoon..."
            if lang in ["hi", "mr"]
            else f"Dispute {dispute_code} registered. I am verifying across bank, NPCI, and Paytm ledger..."
        )

        return AwaitableDict({
            "channel": channel,
            "user_id": uid,
            "dispute_id": dispute.id,
            "dispute_code": dispute.dispute_code,
            "needs_more_info": False,
            "agent_message": agent_msg,
            "entities": entities,
            "transcript": message,
            "ocr_json": None,
        })
    finally:
        if close_db:
            db.close()


def process_voice_message(
    sender_phone: Optional[str],
    user_id: Optional[int],
    filename: str,
    content: bytes,
    channel: str = "SIMULATOR",
    db: Optional[Session] = None,
) -> AwaitableDict:
    """Ingests voice note, performs mock/Sarvam STT, and initiates dispute if UTR is extracted."""
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    try:
        user_info = _resolve_user_id(db, sender_phone, user_id)
        if not user_info:
            return AwaitableDict({
                "channel": channel,
                "user_id": None,
                "dispute_id": None,
                "dispute_code": None,
                "needs_more_info": True,
                "agent_message": "This number is not registered for the demo. Please select a demo user or use a registered WhatsApp number.",
                "entities": ExtractedEntity(),
                "transcript": None,
                "ocr_json": None,
            })

        uid = user_info["user_id"]
        lang = user_info.get("language", "hi")

        voice_res = transcribe_voice(filename=filename, content=content, default_language=lang)
        transcript = voice_res["transcript"]
        entities = voice_res["entities"]

        if not entities.utr:
            prompt = (
                "Aapki voice note receive hui par 12-digit UTR clear nahi hai. Kripya UTR share karein ya screenshot bhein."
                if lang in ["hi", "mr"]
                else "Voice note received, but 12-digit UTR was not detected. Please share the UTR or upload a screenshot."
            )
            return AwaitableDict({
                "channel": channel,
                "user_id": uid,
                "dispute_id": None,
                "dispute_code": None,
                "needs_more_info": True,
                "agent_message": prompt,
                "entities": entities,
                "transcript": transcript,
                "ocr_json": None,
            })

        txn = db.query(Transaction).filter(Transaction.utr == entities.utr).first()
        claimed_amount = entities.amount if entities.amount is not None else (txn.amount if txn else None)
        amount = claimed_amount if claimed_amount is not None else (txn.amount if txn else 0.0)

        dispute_code = f"DISP-{uuid4().hex[:8].upper()}"
        intent_val = entities.intent.value if hasattr(entities.intent, "value") else str(entities.intent)
        dispute = Dispute(
            dispute_code=dispute_code,
            user_id=uid,
            transaction_id=txn.id if txn else None,
            utr=entities.utr,
            claimed_amount=claimed_amount,
            amount=amount,
            channel=channel,
            intent=intent_val,
            language=entities.language or lang,
            transcript=transcript,
            status=DisputeStatus.PENDING.value,
            agent_decision=AgentDecision.PENDING_ANALYSIS.value,
            identity_verified=False,
        )
        db.add(dispute)
        db.commit()
        db.refresh(dispute)

        agent_msg = (
            f"Voice note process ho gayi. Dispute {dispute_code} register kiya gaya hai. Main reconciliation run kar raha hoon..."
            if lang in ["hi", "mr"]
            else f"Voice note processed. Dispute {dispute_code} registered. Verifying against banking ledgers..."
        )

        return AwaitableDict({
            "channel": channel,
            "user_id": uid,
            "dispute_id": dispute.id,
            "dispute_code": dispute.dispute_code,
            "needs_more_info": False,
            "agent_message": agent_msg,
            "entities": entities,
            "transcript": transcript,
            "ocr_json": None,
        })
    finally:
        if close_db:
            db.close()


def process_image_message(
    sender_phone: Optional[str],
    user_id: Optional[int],
    filename: str,
    content: bytes,
    channel: str = "SIMULATOR",
    db: Optional[Session] = None,
) -> AwaitableDict:
    """Ingests screenshot, executes OCR extraction, and creates dispute if UTR is found."""
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    try:
        user_info = _resolve_user_id(db, sender_phone, user_id)
        if not user_info:
            return AwaitableDict({
                "channel": channel,
                "user_id": None,
                "dispute_id": None,
                "dispute_code": None,
                "needs_more_info": True,
                "agent_message": "This number is not registered for the demo. Please select a demo user or use a registered WhatsApp number.",
                "entities": ExtractedEntity(),
                "transcript": None,
                "ocr_json": None,
            })

        uid = user_info["user_id"]
        lang = user_info.get("language", "hi")

        ocr_res = extract_ocr_from_image(filename=filename, content=content)
        ocr_data = ocr_res["ocr_json"]
        entities = ocr_res["entities"]

        if not entities.utr:
            prompt = (
                "Screenshot se 12-digit UTR read nahi ho paya. Kripya saaf screenshot bhejein ya text mein UTR likhein."
                if lang in ["hi", "mr"]
                else "Could not detect a valid 12-digit UTR from the screenshot. Please upload a clear receipt or enter the UTR."
            )
            return AwaitableDict({
                "channel": channel,
                "user_id": uid,
                "dispute_id": None,
                "dispute_code": None,
                "needs_more_info": True,
                "agent_message": prompt,
                "entities": entities,
                "transcript": entities.raw_text,
                "ocr_json": ocr_data,
            })

        txn = db.query(Transaction).filter(Transaction.utr == entities.utr).first()
        claimed_amount = entities.amount if entities.amount is not None else (txn.amount if txn else None)
        amount = claimed_amount if claimed_amount is not None else (txn.amount if txn else 0.0)

        dispute_code = f"DISP-{uuid4().hex[:8].upper()}"
        intent_val = entities.intent.value if hasattr(entities.intent, "value") else str(entities.intent)
        dispute = Dispute(
            dispute_code=dispute_code,
            user_id=uid,
            transaction_id=txn.id if txn else None,
            utr=entities.utr,
            claimed_amount=claimed_amount,
            amount=amount,
            channel=channel,
            intent=intent_val,
            language=entities.language or lang,
            transcript=entities.raw_text,
            ocr_json=json.dumps(ocr_data),
            status=DisputeStatus.PENDING.value,
            agent_decision=AgentDecision.PENDING_ANALYSIS.value,
            identity_verified=False,
        )
        db.add(dispute)
        db.commit()
        db.refresh(dispute)

        agent_msg = (
            f"Screenshot verify ho gaya. Dispute {dispute_code} register kiya gaya hai. Main banking truth check kar raha hoon..."
            if lang in ["hi", "mr"]
            else f"Screenshot verified. Dispute {dispute_code} registered. Performing three-way reconciliation..."
        )

        return AwaitableDict({
            "channel": channel,
            "user_id": uid,
            "dispute_id": dispute.id,
            "dispute_code": dispute.dispute_code,
            "needs_more_info": False,
            "agent_message": agent_msg,
            "entities": entities,
            "transcript": entities.raw_text,
            "ocr_json": ocr_data,
        })
    finally:
        if close_db:
            db.close()
