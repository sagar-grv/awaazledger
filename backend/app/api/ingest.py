"""Multimodal ingestion endpoints supporting text, voice notes, screenshots, and demo scenarios."""

from typing import Optional, Dict, Any, List
from fastapi import APIRouter, UploadFile, File, Form, Depends, Request, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.ingest import (
    IngestTextRequest,
    IngestDemoTextRequest,
    IngestUnifiedResponse,
)
from app.services.channel_identity_service import get_demo_users_for_frontend
from app.services.channel_message_service import (
    process_text_message,
    process_voice_message,
    process_image_message,
)

router = APIRouter(prefix="/ingest", tags=["Multimodal Ingestion"])


_DEMO_SCENARIO_TEXTS = {
    "SCN-01": "भैया मैंने 450 रुपये का payment किया, account से कट गया लेकिन दुकानदार को नहीं मिला। UTR 987654321012 है।",
    "SCN-02": "Maine ₹120 Gupta Medical ko bheja tha par fail ho gaya. UTR 112233445566.",
    "SCN-03": "I paid INR 18,500 for flight ticket but merchant did not receive. UTR 998877665544.",
    "SCN-04": "₹350 ka payment 3 din se pending hai. UTR 445566778899. Merchant not credited.",
    "SCN-05": "Mera 1999 rupaye kata hai. UTR 000000000000.",
    "EDGE-01": "780 rupees payment kiya tha Reliance Fresh ko par app me pending dikh raha hai. UTR 556677889900.",
    "SCN-EDGE-01": "780 rupees payment kiya tha Reliance Fresh ko par app me pending dikh raha hai. UTR 556677889900.",
    "EDGE-02": "Do baar ₹650 cut ho gaye petrol pump par. UTR 778899001123.",
    "SCN-EDGE-02": "Do baar ₹650 cut ho gaye petrol pump par. UTR 778899001123.",
    "EDGE-03": "Maine 5000 pay kiya CCD me par bank se 500 debit hua. UTR 334455667788.",
    "SCN-EDGE-03": "Maine 5000 pay kiya CCD me par bank se 500 debit hua. UTR 334455667788.",
}


@router.post("/text", response_model=IngestUnifiedResponse)
def ingest_text(
    payload: Optional[IngestTextRequest] = None,
    sender_phone: Optional[str] = Form(None),
    user_id: Optional[int] = Form(None),
    message: Optional[str] = Form(None),
    channel: Optional[str] = Form("SIMULATOR"),
    db: Session = Depends(get_db),
):
    """Ingests plain text complaints via JSON payload or Form data."""
    if payload:
        s_phone = payload.sender_phone
        u_id = payload.user_id
        msg = payload.message
        chn = payload.channel
    else:
        s_phone = sender_phone
        u_id = user_id
        msg = message or ""
        chn = channel or "SIMULATOR"

    if not (msg or "").strip():
        raise HTTPException(status_code=400, detail="Message text is required.")

    result = process_text_message(
        sender_phone=s_phone,
        user_id=u_id,
        message=msg,
        channel=chn,
        db=db,
    )
    return result


@router.post("/voice", response_model=IngestUnifiedResponse)
def ingest_voice(
    file: UploadFile = File(...),
    sender_phone: Optional[str] = Form(None),
    user_id: Optional[int] = Form(None),
    channel: str = Form("SIMULATOR"),
    db: Session = Depends(get_db),
):
    """Ingests vernacular voice notes, performs STT/mock transcription, and initializes dispute."""
    content = file.file.read()
    result = process_voice_message(
        sender_phone=sender_phone,
        user_id=user_id,
        filename=file.filename or "voice_recording.ogg",
        content=content,
        channel=channel,
        db=db,
    )
    return result


@router.post("/image", response_model=IngestUnifiedResponse)
@router.post("/screenshot", response_model=IngestUnifiedResponse)
def ingest_image(
    file: UploadFile = File(...),
    sender_phone: Optional[str] = Form(None),
    user_id: Optional[int] = Form(None),
    channel: str = Form("SIMULATOR"),
    db: Session = Depends(get_db),
):
    """Ingests payment screenshot receipts, runs OCR, and extracts dispute fields."""
    content = file.file.read()
    result = process_image_message(
        sender_phone=sender_phone,
        user_id=user_id,
        filename=file.filename or "receipt.jpg",
        content=content,
        channel=channel,
        db=db,
    )
    return result


@router.post("/demo-text", response_model=IngestUnifiedResponse)
def ingest_demo_text(
    payload: IngestDemoTextRequest,
    db: Session = Depends(get_db),
):
    """Convenience endpoint triggering scenario-based text ingestion for simulator buttons."""
    scenario_key = payload.scenario.strip().upper()
    msg = _DEMO_SCENARIO_TEXTS.get(
        scenario_key,
        f"Dispute for {scenario_key} payment not received. UTR 987654321012.",
    )

    result = process_text_message(
        sender_phone=None,
        user_id=payload.user_id,
        message=msg,
        channel="SIMULATOR",
        db=db,
    )
    return result


@router.get("/demo-users", response_model=List[Dict[str, Any]])
def get_demo_users():
    """Returns pre-configured demo user accounts mapped to WhatsApp demo numbers."""
    return get_demo_users_for_frontend()
