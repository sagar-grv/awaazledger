"""Action database model."""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from app.db.base import Base


class Action(Base):
    __tablename__ = "actions"

    id = Column(Integer, primary_key=True, index=True)
    dispute_id = Column(Integer, ForeignKey("disputes.id"), nullable=False)
    action_type = Column(String(64), nullable=False)
    payload_json = Column(Text, nullable=True)
    executed_by = Column(String(64), default="AI_AGENT")
    status = Column(String(32), default="COMPLETED")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
