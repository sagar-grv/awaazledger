"""User schemas."""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class UserBase(BaseModel):
    name: str
    mobile_hash: str
    paytm_id: str
    language: str = "hi"
    trust_score: int = 100
    kyc_status: str = "VERIFIED"
    device_id: Optional[str] = None
    blacklisted: bool = False
    previous_dispute_count: int = 0


class UserCreate(UserBase):
    pass


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class TrustProfileResponse(BaseModel):
    user_id: int
    trust_score: int
    kyc_status: str
    blacklisted: bool
    device_consistent: bool
    previous_dispute_count: int
    risk_band: str  # LOW, MEDIUM, HIGH, CRITICAL
    recent_dispute_count: int
    fraud_history_flag: bool
    velocity_flag: bool
