"""Pydantic schemas for Voice Call AI Teammate."""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class CallInitiateRequest(BaseModel):
    caller_phone: Optional[str] = Field(None, description="E.164 phone number of caller")
    user_id: Optional[int] = Field(None, description="Pre-identified user ID if known")
    language: Optional[str] = Field("hi", description="hi, mr, or en")
    channel: Optional[str] = Field("BROWSER_WEBRTC", description="BROWSER_WEBRTC, FREESWITCH, ASTERISK, SIP")


class CallTurnRequest(BaseModel):
    transcript: Optional[str] = Field("", description="Transcribed caller speech text")
    audio_base64: Optional[str] = Field(None, description="Raw audio chunk encoded in Base64")
    dtmf_digit: Optional[str] = Field(None, description="DTMF keypad key (0-9, *, #)")
    confidence: Optional[float] = Field(1.0, description="ASR confidence score")


class CallTurnResponse(BaseModel):
    call_sid: str
    turn_index: int
    current_state: str
    agent_speech: str
    agent_speech_en: Optional[str] = None
    audio_base64: Optional[str] = None
    audio_url: Optional[str] = None
    language: str = "hi"
    dispute_code: Optional[str] = None
    dispute_status: Optional[str] = None
    claimed_amount: Optional[float] = None
    utr: Optional[str] = None
    prompt_dtmf: bool = False
    is_final: bool = False
    resolution_data: Optional[Dict[str, Any]] = None


class CallDtmfRequest(BaseModel):
    digit: str = Field(..., max_length=16, description="DTMF keypress or digit sequence")


class CallFeedbackRequest(BaseModel):
    rating: str = Field(..., description="1-5 rating or HELPFUL/NOT_HELPFUL/HUMAN_REQUEST")
    feedback_type: Optional[str] = Field("VOICE", description="VOICE, DTMF, UI")
    transcript: Optional[str] = Field(None, description="Spoken feedback remarks")


class CallSessionResponse(BaseModel):
    call_sid: str
    channel: str
    caller_phone: Optional[str]
    user_id: Optional[int]
    language: str
    consent_given: bool
    status: str
    current_state: str
    dispute_id: Optional[int]
    dispute_code: Optional[str]
    claimed_amount: Optional[float]
    utr: Optional[str]
    start_time: datetime
    end_time: Optional[datetime]
    duration_seconds: int

    model_config = {"from_attributes": True}


class LiveCallSummary(BaseModel):
    call_sid: str
    channel: str
    caller_phone_masked: str
    current_state: str
    language: str
    duration_seconds: int
    turn_count: int
    latest_caller_text: Optional[str] = None
    latest_agent_speech: Optional[str] = None
    dispute_code: Optional[str] = None
    status: str
