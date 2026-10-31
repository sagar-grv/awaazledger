"""Escalation schemas for supervisor human-in-the-loop workflows."""

from typing import Optional, List, Any, Dict
from datetime import datetime, timezone
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field


class EscalationStatus(str, Enum):
    OPEN = "OPEN"
    IN_REVIEW = "IN_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    INFO_REQUESTED = "INFO_REQUESTED"
    FRAUD_CONFIRMED = "FRAUD_CONFIRMED"


class EscalationPriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class EscalationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    dispute_id: int
    dispute_code: Optional[str] = None
    user_name: Optional[str] = None
    user_phone: Optional[str] = None
    amount: Optional[float] = 0.0
    priority: str = "MEDIUM"
    reason: str
    assigned_to: Optional[str] = None
    sla_deadline: Optional[datetime] = None
    status: str = "OPEN"
    resolution_note: Optional[str] = None
    resolution_notes: Optional[str] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    is_sla_breached: bool = False
    hours_to_sla: Optional[float] = None


class EscalationListResponse(BaseModel):
    items: List[EscalationResponse]
    total: int
    open_count: int
    sla_breached_count: int


class EscalationDetailResponse(BaseModel):
    escalation: EscalationResponse
    dispute: Dict[str, Any]
    user: Dict[str, Any]
    transaction: Optional[Dict[str, Any]] = None
    three_way_reconciliation: Optional[Dict[str, Any]] = None
    risk_assessment: Optional[Dict[str, Any]] = None
    policy_evaluation: Optional[Dict[str, Any]] = None
    actions_taken: List[Dict[str, Any]] = Field(default_factory=list)
    audit_trail: List[Dict[str, Any]] = Field(default_factory=list)
    evidence_items: List[Dict[str, Any]] = Field(default_factory=list)


class SupervisorActionRequest(BaseModel):
    note: Optional[str] = None
    supervisor_id: Optional[str] = "SUPERVISOR_L2"
    action_reason: Optional[str] = None
    requested_info_prompt: Optional[str] = None


class SupervisorAssignRequest(BaseModel):
    assigned_to: str
    supervisor_id: Optional[str] = "SUPERVISOR_L2"
    note: Optional[str] = None


class SupervisorActionResponse(BaseModel):
    escalation_id: int
    dispute_id: int
    action: str
    status: str
    message: str
    bridge_credit_id: Optional[int] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EscalationResolveRequest(BaseModel):
    resolution_notes: Optional[str] = None
    approved: bool = True
