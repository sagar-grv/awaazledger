"""Dispute database model."""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Text, Boolean, DateTime, ForeignKey
from app.db.base import Base


class Dispute(Base):
    __tablename__ = "disputes"

    id = Column(Integer, primary_key=True, index=True)
    dispute_code = Column(String(64), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=True)
    utr = Column(String(64), index=True, nullable=True)
    claimed_amount = Column(Float, nullable=True)
    amount = Column(Float, default=0.0)
    channel = Column(String(32), default="SIMULATOR")
    intent = Column(String(64), default="DISPUTE_COMPLAINT")
    language = Column(String(10), default="hi")
    transcript = Column(Text, nullable=True)
    ocr_json = Column(Text, nullable=True)
    status = Column(String(32), default="PENDING")
    agent_decision = Column(String(32), default="PENDING_ANALYSIS")
    risk_score = Column(Float, default=0.0)
    fraud_score = Column(Float, default=0.0)
    risk_level = Column(String(32), default="UNKNOWN")
    confidence_score = Column(Float, default=0.0)
    identity_verified = Column(Boolean, default=False)
    consent_id = Column(Integer, nullable=True)
    three_way_json = Column(Text, nullable=True)
    explanation_user = Column(Text, nullable=True)
    explanation_internal = Column(Text, nullable=True)
    state_history_json = Column(Text, nullable=True)
    recommended_actions_json = Column(Text, nullable=True)
    action_summary_json = Column(Text, nullable=True)
    idempotency_prefix = Column(String(64), nullable=True)
    assigned_agent = Column(String(64), default="AI_TEAMMATE")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    resolved_at = Column(DateTime, nullable=True)
