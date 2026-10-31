"""SQLAlchemy model for end-of-call user feedback."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.db.base import Base


class CallFeedback(Base):
    __tablename__ = "call_feedbacks"

    id = Column(Integer, primary_key=True, index=True)
    call_session_id = Column(Integer, ForeignKey("call_sessions.id", ondelete="CASCADE"), index=True, nullable=False)
    caller_phone = Column(String(32), nullable=True)
    rating = Column(String(32), nullable=False)  # "1", "2", "HELPFUL", "NOT_HELPFUL", "HUMAN_REQUEST"
    feedback_type = Column(String(16), default="VOICE", nullable=False)  # "VOICE", "DTMF", "UI"
    transcript = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    session = relationship("CallSession", back_populates="feedbacks")
