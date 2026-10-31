"""SQLAlchemy model for individual dialog turns in a Voice Call session."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.db.base import Base


class CallTurn(Base):
    __tablename__ = "call_turns"

    id = Column(Integer, primary_key=True, index=True)
    call_session_id = Column(Integer, ForeignKey("call_sessions.id", ondelete="CASCADE"), index=True, nullable=False)
    turn_index = Column(Integer, default=0, nullable=False)
    speaker = Column(String(16), nullable=False)  # "CALLER", "AGENT"
    transcript = Column(Text, nullable=False)
    confidence = Column(Float, default=1.0, nullable=False)
    dtmf_digit = Column(String(8), nullable=True)
    action_taken = Column(String(64), nullable=True)
    audio_url = Column(String(256), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    session = relationship("CallSession", back_populates="turns")
