"""Customer Feedback database model."""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from app.db.base import Base


class Feedback(Base):
    __tablename__ = "feedbacks"

    id = Column(Integer, primary_key=True, index=True)
    dispute_id = Column(Integer, ForeignKey("disputes.id", ondelete="CASCADE"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    phone_hash = Column(String(64), nullable=True, index=True)
    rating = Column(String(32), nullable=False)  # HELPFUL, NOT_HELPFUL, HUMAN_REQUEST, WRONG_DECISION
    comment = Column(Text, nullable=True)
    source = Column(String(32), default="WHATSAPP")  # WHATSAPP, DASHBOARD, API
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
