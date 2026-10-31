"""Reconciliation schemas."""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class ReconciliationFacts(BaseModel):
    utr: str
    user_id: int
    identity_match: bool
    cbs_found: bool
    cbs_debited: bool
    cbs_amount: Optional[float] = None
    claimed_amount: Optional[float] = None
    amount_matches: bool
    amount_mismatch: bool
    npcI_found: bool
    npcI_status: Optional[str] = None
    failure_point: Optional[str] = None
    beneficiary_credited: bool
    merchant_credit_status: Optional[str] = None
    paytm_settlement_status: Optional[str] = None
    auto_reversal_scheduled: bool
    ghost_success: bool
    duplicate_debit: bool
    duplicate_utrs: List[str] = []
    invalid_utr: bool
    user_mismatch: bool
    risk_signals: Dict[str, Any]
    policy_inputs: Dict[str, Any]
    raw: Optional[Dict[str, Any]] = None


class ThreeWayCheckRequest(BaseModel):
    utr: str
    user_id: int
    claimed_amount: Optional[float] = None
    channel: str = "SIMULATOR"


class ThreeWayCheckResponse(BaseModel):
    facts: ReconciliationFacts
