"""Agent execution schemas."""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from app.schemas.dispute import AgentDecision, ActionType, RiskLevel, DisputeStatus


class RiskResult(BaseModel):
    fraud_score: float
    risk_score: float
    risk_level: RiskLevel
    signals: Dict[str, Any]
    reasons: List[str]


class PolicyDecision(BaseModel):
    decision: AgentDecision
    actions: List[ActionType]
    rule_matched: str
    eligible_for_bridge_credit: bool
    requires_human_review: bool
    fraud_block: bool
    info_request: bool
    reasons: List[str]


class ActionExecutionResult(BaseModel):
    action_type: ActionType
    status: str
    payload: Dict[str, Any]


class AgentRunRequest(BaseModel):
    dispute_id: int
    simulate_speed_ms: Optional[int] = 0


class AgentRunResponse(BaseModel):
    dispute_id: int
    dispute_code: str
    utr: str
    user_id: int
    amount: float
    decision: AgentDecision
    risk_level: RiskLevel
    fraud_score: float
    risk_score: float
    actions_executed: List[ActionExecutionResult]
    explanation_user: str
    explanation_internal: str
    three_way: Dict[str, Any]
    risk: Dict[str, Any]
    policy: Dict[str, Any]
    state_history: List[Dict[str, Any]]
    status: DisputeStatus
    resolved: bool


class AgentStateInfo(BaseModel):
    dispute_id: int
    current_state: str
    history: List[Dict[str, Any]]
