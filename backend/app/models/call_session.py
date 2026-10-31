"""SQLAlchemy model for Voice Call AI Teammate sessions."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.db.base import Base


class CallSession(Base):
    __tablename__ = "call_sessions"

    id = Column(Integer, primary_key=True, index=True)
    call_sid = Column(String(64), unique=True, index=True, nullable=False)
    channel = Column(String(32), default="BROWSER_WEBRTC", nullable=False)
    caller_phone = Column(String(32), nullable=True)
    phone_hash = Column(String(64), index=True, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    language = Column(String(8), default="hi", nullable=False)
    consent_given = Column(Boolean, default=False, nullable=False)
    status = Column(String(32), default="IN_PROGRESS", nullable=False)
    current_state = Column(String(64), default="GREETING_CONSENT", nullable=False)
    dispute_id = Column(Integer, ForeignKey("disputes.id"), nullable=True)
    dispute_code = Column(String(32), nullable=True)
    claimed_amount = Column(Float, nullable=True)
    utr = Column(String(32), nullable=True)
    start_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    end_time = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship("User", backref="call_sessions")
    dispute = relationship("Dispute", backref="call_sessions")
    turns = relationship("CallTurn", back_populates="session", cascade="all, delete-orphan", order_by="CallTurn.turn_index")
    feedbacks = relationship("CallFeedback", back_populates="session", cascade="all, delete-orphan")
