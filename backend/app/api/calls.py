"""API Endpoints for Voice Call AI Teammate and Telephony WebSockets."""

import json
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.call import (
    CallInitiateRequest,
    CallTurnRequest,
    CallTurnResponse,
    CallDtmfRequest,
    CallFeedbackRequest,
    CallSessionResponse,
    LiveCallSummary,
)
from app.services.voice_agent_service import VoiceAgentService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/calls", tags=["Voice Call Teammate"])


@router.post("/initiate", response_model=CallTurnResponse)
def initiate_call(req: CallInitiateRequest, db: Session = Depends(get_db)):
    """Initiates a voice call session and returns the initial identity/consent greeting."""
    svc = VoiceAgentService(db)
    session = svc.initiate_call(
        caller_phone=req.caller_phone,
        user_id=req.user_id,
        channel=req.channel or "BROWSER_WEBRTC",
        language=req.language or "hi",
    )
    greeting = svc.start_dialog(session.call_sid)
    return CallTurnResponse(**greeting)


@router.post("/{call_sid}/turn", response_model=CallTurnResponse)
def process_call_turn(call_sid: str, req: CallTurnRequest, db: Session = Depends(get_db)):
    """Processes caller speech or DTMF and returns AI agent's spoken response and resolution state."""
    svc = VoiceAgentService(db)
    try:
        res = svc.process_turn(
            call_sid=call_sid,
            transcript=req.transcript or "",
            dtmf_digit=req.dtmf_digit,
            confidence=req.confidence or 1.0,
        )
        return CallTurnResponse(**res)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{call_sid}/dtmf", response_model=CallTurnResponse)
def send_dtmf_digit(call_sid: str, req: CallDtmfRequest, db: Session = Depends(get_db)):
    """Handles caller dialpad DTMF keypress."""
    svc = VoiceAgentService(db)
    try:
        res = svc.process_dtmf(call_sid, req.digit)
        return CallTurnResponse(**res)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{call_sid}/end", response_model=CallSessionResponse)
def end_call(call_sid: str, db: Session = Depends(get_db)):
    """Ends the active voice call session and records total duration."""
    svc = VoiceAgentService(db)
    try:
        session = svc.end_call(call_sid)
        return CallSessionResponse.model_validate(session)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{call_sid}/feedback")
def submit_call_feedback(call_sid: str, req: CallFeedbackRequest, db: Session = Depends(get_db)):
    """Submits caller feedback rating."""
    svc = VoiceAgentService(db)
    try:
        fb = svc.submit_feedback(
            call_sid=call_sid,
            rating=req.rating,
            feedback_type=req.feedback_type or "VOICE",
            transcript=req.transcript,
        )
        return {"status": "SUCCESS", "feedback_id": fb.id, "rating": fb.rating}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/live", response_model=List[LiveCallSummary])
def get_live_calls(db: Session = Depends(get_db)):
    """Returns active and recent calls for the supervisor live console."""
    svc = VoiceAgentService(db)
    return svc.list_active_calls()


@router.get("/{call_sid}/status", response_model=CallSessionResponse)
def get_call_status(call_sid: str, db: Session = Depends(get_db)):
    """Returns current call session metadata."""
    svc = VoiceAgentService(db)
    session = svc.get_session(call_sid)
    if not session:
        raise HTTPException(status_code=404, detail=f"Call {call_sid} not found")
    return CallSessionResponse.model_validate(session)


@router.post("/webhook/telephony")
def telephony_sip_webhook(payload: Dict[str, Any], db: Session = Depends(get_db)):
    """Universal SIP Trunk / FreeSWITCH / Asterisk / LiveKit webhook gateway."""
    svc = VoiceAgentService(db)
    caller = payload.get("caller") or payload.get("from") or payload.get("From") or "+918788021157"
    call_sid = payload.get("call_sid") or payload.get("CallSid")

    if not call_sid:
        session = svc.initiate_call(caller_phone=caller, channel="FREESWITCH")
        greeting = svc.start_dialog(session.call_sid)
        return {
            "status": "INITIATED",
            "call_sid": session.call_sid,
            "play_speech": greeting["agent_speech"],
            "prompt_dtmf": True,
        }

    dtmf = payload.get("dtmf") or payload.get("Digits")
    speech_text = payload.get("transcript") or payload.get("SpeechResult") or ""

    turn = svc.process_turn(call_sid=call_sid, transcript=speech_text, dtmf_digit=dtmf)
    return {
        "status": "IN_PROGRESS",
        "call_sid": call_sid,
        "play_speech": turn["agent_speech"],
        "is_final": turn.get("is_final", False),
    }


@router.websocket("/ws/{call_sid}")
async def websocket_call_endpoint(websocket: WebSocket, call_sid: str, db: Session = Depends(get_db)):
    """Real-time duplex WebSocket for streaming browser WebRTC audio or SIP packets."""
    await websocket.accept()
    svc = VoiceAgentService(db)

    try:
        # Send initial greeting
        session = svc.get_session(call_sid)
        if not session:
            session = svc.initiate_call(caller_phone="+918788021157", channel="BROWSER_WEBRTC")
            call_sid = session.call_sid

        greeting = svc.start_dialog(call_sid)
        await websocket.send_json({
            "event": "agent_speech",
            "data": greeting,
        })

        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            event = msg.get("event")

            if event == "caller_turn":
                transcript = msg.get("transcript", "")
                dtmf = msg.get("dtmf")
                res = svc.process_turn(call_sid=call_sid, transcript=transcript, dtmf_digit=dtmf)
                await websocket.send_json({
                    "event": "agent_speech",
                    "data": res,
                })
                if res.get("is_final"):
                    break

            elif event == "dtmf":
                digit = str(msg.get("digit", ""))
                res = svc.process_dtmf(call_sid=call_sid, digit=digit)
                await websocket.send_json({
                    "event": "agent_speech",
                    "data": res,
                })
                if res.get("is_final"):
                    break

            elif event == "end_call":
                svc.end_call(call_sid)
                await websocket.send_json({"event": "call_ended", "call_sid": call_sid})
                break

    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected for call {call_sid}")
    except Exception as e:
        logger.error(f"WebSocket error in call {call_sid}: {e}")
    finally:
        try:
            svc.end_call(call_sid)
        except Exception:
            pass
