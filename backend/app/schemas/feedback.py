"""Schemas for customer feedback tracking and satisfaction analytics."""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class FeedbackCreate(BaseModel):
    dispute_id: Optional[int] = None
    user_id: Optional[int] = None
    phone: Optional[str] = None
    rating: str  # HELPFUL, NOT_HELPFUL, HUMAN_REQUEST, WRONG_DECISION
    comment: Optional[str] = None
    source: str = "WHATSAPP"


class FeedbackResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    dispute_id: Optional[int] = None
    user_id: Optional[int] = None
    phone_hash: Optional[str] = None
    rating: str
    comment: Optional[str] = None
    source: str
    created_at: datetime


class FeedbackSummary(BaseModel):
    total_feedback: int = 0
    helpful_count: int = 0
    not_helpful_count: int = 0
    human_request_count: int = 0
    wrong_decision_count: int = 0
    customer_satisfaction_pct: float = 100.0
    pending_feedback_count: int = 0
