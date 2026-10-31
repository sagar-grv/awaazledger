"""Pydantic schemas for multimodal channel ingestion and intent extraction."""

from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class IntentType(str, Enum):
    UPI_PENDING_DISPUTE = "UPI_PENDING_DISPUTE"
    STATUS_CHECK = "STATUS_CHECK"
    FRAUD_REPORT = "FRAUD_REPORT"
    HUMAN_REQUEST = "HUMAN_REQUEST"
    MERCHANT_RECEIPT_HELP = "MERCHANT_RECEIPT_HELP"
    UNKNOWN = "UNKNOWN"


class ExtractedEntity(BaseModel):
    utr: Optional[str] = None
    amount: Optional[float] = None
    currency: str = "INR"
    bank: Optional[str] = None
    merchant_name: Optional[str] = None
    timestamp: Optional[str] = None
    language: Optional[str] = None
    intent: IntentType = IntentType.UNKNOWN
    confidence: float = 0.0
    missing_fields: List[str] = Field(default_factory=list)
    raw_text: Optional[str] = None


class IngestTextRequest(BaseModel):
    sender_phone: Optional[str] = None
    user_id: Optional[int] = None
    message: str
    channel: str = "SIMULATOR"


class IngestVoiceResponse(BaseModel):
    transcript: str
    language: Optional[str] = None
    entities: ExtractedEntity
    user_id: Optional[int] = None
    dispute_id: Optional[int] = None
    dispute_code: Optional[str] = None
    needs_more_info: bool = False
    agent_message: str


class IngestImageResponse(BaseModel):
    ocr_json: Dict[str, Any]
    entities: ExtractedEntity
    user_id: Optional[int] = None
    dispute_id: Optional[int] = None
    dispute_code: Optional[str] = None
    needs_more_info: bool = False
    agent_message: str


class IngestUnifiedResponse(BaseModel):
    channel: str
    user_id: Optional[int] = None
    dispute_id: Optional[int] = None
    dispute_code: Optional[str] = None
    needs_more_info: bool = False
    agent_message: str
    entities: ExtractedEntity
    transcript: Optional[str] = None
    ocr_json: Optional[Dict[str, Any]] = None


class IngestDemoTextRequest(BaseModel):
    user_id: int
    scenario: str
