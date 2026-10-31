"""Dispute Pydantic schemas and core domain enums."""

from enum import Enum
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class DisputeStatus(str, Enum):
    PENDING = "PENDING"
    ANALYZING = "ANALYZING"
    AUTO_CREDITED = "AUTO_CREDITED"
    ESCALATED = "ESCALATED"
    RESOLVED = "RESOLVED"
    REJECTED = "REJECTED"
    FRAUD_BLOCKED = "FRAUD_BLOCKED"
    RECEIPT_GENERATED = "RECEIPT_GENERATED"
    INFO_REQUESTED = "INFO_REQUESTED"


class AgentDecision(str, Enum):
    AUTO_RESOLVE = "AUTO_RESOLVE"
    HUMAN_ESCALATE = "HUMAN_ESCALATE"
    FRAUD_BLOCK = "FRAUD_BLOCK"
    INFO_REQUEST = "INFO_REQUEST"
    PENDING_ANALYSIS = "PENDING_ANALYSIS"


class ActionType(str, Enum):
    BRIDGE_CREDIT = "BRIDGE_CREDIT"
    REVERSAL_REQUEST = "REVERSAL_REQUEST"
    NPCI_DISPUTE_RAISED = "NPCI_DISPUTE_RAISED"
    RBI_PENALTY_CLAIM = "RBI_PENALTY_CLAIM"
    NOTIFY_USER = "NOTIFY_USER"
    ESCALATE_HUMAN = "ESCALATE_HUMAN"
    GENERATE_RECEIPT = "GENERATE_RECEIPT"
    FRAUD_ALERT = "FRAUD_ALERT"
    REQUEST_INFO = "REQUEST_INFO"
    START_RBI_TAT_TIMER = "START_RBI_TAT_TIMER"
    CLOSE_DISPUTE = "CLOSE_DISPUTE"
    MERCHANT_RECOVERY_LINK = "MERCHANT_RECOVERY_LINK"
    SWARM_SHIELD_ADVISORY = "SWARM_SHIELD_ADVISORY"
    GUIDED_DEMO_STEP = "GUIDED_DEMO_STEP"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    UNKNOWN = "UNKNOWN"


class ChannelType(str, Enum):
    WHATSAPP = "WHATSAPP"
    VOICE_IVR = "VOICE_IVR"
    SIMULATOR = "SIMULATOR"
    WEB_PORTAL = "WEB_PORTAL"


class TransactionStatus(str, Enum):
    SUCCESS = "SUCCESS"
    PENDING = "PENDING"
    FAILED = "FAILED"
    REVERSED = "REVERSED"
    DEEMED = "DEEMED"


class NpciStatus(str, Enum):
    SUCCESS = "SUCCESS"
    U30 = "U30"
    U69 = "U69"
    INVALID_UTR = "INVALID_UTR"
    BENEFICIARY_TIMEOUT = "BENEFICIARY_TIMEOUT"
    DEEMED_APPROVED = "DEEMED_APPROVED"


class SettlementStatus(str, Enum):
    SETTLED = "SETTLED"
    PENDING = "PENDING"
    FAILED = "FAILED"
    IN_TRANSIT = "IN_TRANSIT"


class DisputeCreateRequest(BaseModel):
    user_id: int
    utr: str
    claimed_amount: Optional[float] = None
    channel: str = "SIMULATOR"
    intent: str = "UPI_PENDING_DISPUTE"
    language: str = "hi"
    transcript: Optional[str] = None
    ocr_json: Optional[str] = None


class DisputeBase(BaseModel):
    user_id: int
    transaction_id: Optional[int] = None
    utr: Optional[str] = None
    claimed_amount: Optional[float] = None
    channel: str = "SIMULATOR"
    intent: str = "DISPUTE_COMPLAINT"
    language: str = "hi"
    description: Optional[str] = None
    amount: float = 0.0


class DisputeCreate(DisputeBase):
    pass


class DisputeDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    dispute_code: str
    user_id: int
    transaction_id: Optional[int] = None
    utr: Optional[str] = None
    claimed_amount: Optional[float] = None
    amount: float = 0.0
    channel: str
    intent: str
    language: str
    status: str
    agent_decision: str
    risk_score: float = 0.0
    fraud_score: float = 0.0
    confidence_score: float = 0.0
    identity_verified: bool = False
    consent_id: Optional[int] = None
    three_way_json: Optional[str] = None
    explanation_user: Optional[str] = None
    explanation_internal: Optional[str] = None
    state_history_json: Optional[str] = None
    risk_level: Optional[str] = "UNKNOWN"
    recommended_actions_json: Optional[str] = None
    action_summary_json: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None


class DisputeResponse(DisputeDetailResponse):
    pass
