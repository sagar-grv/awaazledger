"""Voice Agent Service for orchestrating spoken call sessions and telephony integration."""

import uuid
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from app.models.call_session import CallSession
from app.models.call_turn import CallTurn
from app.models.call_feedback import CallFeedback
from app.calls.call_state_machine import CallDialogManager
from app.services.feedback_service import hash_phone
from app.services.sarvam_tts import generate_voice_reply
from app.core.config import settings

logger = logging.getLogger(__name__)


class VoiceAgentService:
    """Orchestrates life-cycle, dialog state machine, and audio synthesis for voice calls."""

    def __init__(self, db: Session):
        self.db = db

    def initiate_call(
        self,
        caller_phone: Optional[str] = None,
        user_id: Optional[int] = None,
        channel: str = "BROWSER_WEBRTC",
        language: str = "hi",
    ) -> CallSession:
        """Creates a new active call session with unique SID."""
        call_sid = f"CALL-{uuid.uuid4().hex[:8].upper()}"
        phone_hash = hash_phone(caller_phone) if caller_phone else None

        session = CallSession(
            call_sid=call_sid,
            channel=channel,
            caller_phone=caller_phone,
            phone_hash=phone_hash,
            user_id=user_id or 1,
            language=language or getattr(settings, "VOICE_CALL_DEFAULT_LANGUAGE", "hi"),
            status="IN_PROGRESS",
            current_state="GREETING_CONSENT",
            start_time=datetime.utcnow(),
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def get_session(self, call_sid: str) -> Optional[CallSession]:
        """Fetches active call session by SID."""
        return self.db.query(CallSession).filter(CallSession.call_sid == call_sid).first()

    def start_dialog(self, call_sid: str) -> Dict[str, Any]:
        """Starts dialog and returns initial greeting with consent prompt."""
        session = self.get_session(call_sid)
        if not session:
            raise ValueError(f"Call session not found for SID: {call_sid}")

        mgr = CallDialogManager(self.db, session)
        greeting = mgr.get_initial_greeting()

        # Try to generate Sarvam voice audio if enabled
        audio_url = None
        if getattr(settings, "ENABLE_SARVAM_REAL", False):
            try:
                audio_url = generate_voice_reply(greeting["agent_speech"], "CALL_GREETING", language=session.language)
            except Exception as e:
                logger.warning(f"Failed to generate Sarvam audio: {e}")

        greeting["call_sid"] = session.call_sid
        greeting["turn_index"] = 1
        greeting["audio_url"] = audio_url
        greeting["is_final"] = False
        return greeting

    def process_turn(
        self,
        call_sid: str,
        transcript: str = "",
        dtmf_digit: Optional[str] = None,
        confidence: float = 1.0,
    ) -> Dict[str, Any]:
        """Processes a spoken or DTMF turn through CallDialogManager."""
        session = self.get_session(call_sid)
        if not session:
            raise ValueError(f"Call session not found for SID: {call_sid}")

        mgr = CallDialogManager(self.db, session)
        turn_res = mgr.process_turn(caller_transcript=transcript, dtmf_digit=dtmf_digit, confidence=confidence)

        # Audio synthesis if Sarvam enabled
        audio_url = None
        if getattr(settings, "ENABLE_SARVAM_REAL", False) and turn_res.get("agent_speech"):
            try:
                audio_url = generate_voice_reply(
                    turn_res["agent_speech"],
                    f"CALL_TURN_{session.current_state}",
                    language=session.language,
                )
            except Exception as e:
                logger.warning(f"Voice synthesis error: {e}")

        turn_count = self.db.query(CallTurn).filter(CallTurn.call_session_id == session.id).count()

        return {
            "call_sid": session.call_sid,
            "turn_index": turn_count,
            "current_state": session.current_state,
            "agent_speech": turn_res.get("agent_speech", ""),
            "agent_speech_en": turn_res.get("agent_speech_en"),
            "audio_url": audio_url,
            "language": session.language,
            "dispute_code": session.dispute_code,
            "dispute_status": turn_res.get("dispute_status"),
            "claimed_amount": session.claimed_amount,
            "utr": session.utr,
            "prompt_dtmf": turn_res.get("prompt_dtmf", False),
            "is_final": turn_res.get("is_final", False),
            "resolution_data": turn_res.get("resolution_data"),
        }

    def process_dtmf(self, call_sid: str, digit: str) -> Dict[str, Any]:
        """Shortcut for DTMF digit keypress."""
        return self.process_turn(call_sid=call_sid, transcript="", dtmf_digit=digit)

    def submit_feedback(self, call_sid: str, rating: str, feedback_type: str = "VOICE", transcript: Optional[str] = None) -> CallFeedback:
        """Records explicit feedback for call."""
        session = self.get_session(call_sid)
        if not session:
            raise ValueError(f"Call session not found for SID: {call_sid}")

        fb = CallFeedback(
            call_session_id=session.id,
            caller_phone=session.caller_phone,
            rating=rating,
            feedback_type=feedback_type,
            transcript=transcript,
        )
        self.db.add(fb)
        self.db.commit()
        self.db.refresh(fb)
        return fb

    def end_call(self, call_sid: str) -> CallSession:
        """Ends an active call session and records duration."""
        session = self.get_session(call_sid)
        if not session:
            raise ValueError(f"Call session not found for SID: {call_sid}")

        session.status = "COMPLETED"
        session.current_state = "ENDED"
        session.end_time = datetime.utcnow()
        if session.start_time:
            session.duration_seconds = int((session.end_time - session.start_time).total_seconds())
        self.db.commit()
        self.db.refresh(session)
        return session

    def list_active_calls(self) -> List[Dict[str, Any]]:
        """Returns active or recent calls for the live supervisor console."""
        calls = self.db.query(CallSession).order_by(CallSession.id.desc()).limit(15).all()
        summary_list = []
        for c in calls:
            turns = self.db.query(CallTurn).filter(CallTurn.call_session_id == c.id).order_by(CallTurn.turn_index.desc()).all()
            latest_caller = None
            latest_agent = None
            for t in turns:
                if not latest_caller and t.speaker == "CALLER":
                    latest_caller = t.transcript
                if not latest_agent and t.speaker == "AGENT":
                    latest_agent = t.transcript
                if latest_caller and latest_agent:
                    break

            phone_masked = (c.caller_phone[:6] + "XXXXXX") if c.caller_phone and len(c.caller_phone) >= 10 else "ANONYMOUS"
            dur = c.duration_seconds
            if c.status == "IN_PROGRESS" and c.start_time:
                dur = int((datetime.utcnow() - c.start_time).total_seconds())

            summary_list.append({
                "call_sid": c.call_sid,
                "channel": c.channel,
                "caller_phone_masked": phone_masked,
                "current_state": c.current_state,
                "language": c.language,
                "duration_seconds": dur,
                "turn_count": len(turns),
                "latest_caller_text": latest_caller,
                "latest_agent_speech": latest_agent,
                "dispute_code": c.dispute_code,
                "status": c.status,
            })
        return summary_list
