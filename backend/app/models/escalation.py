"""Escalation database model."""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from app.db.base import Base


class Escalation(Base):
    __tablename__ = "escalations"

    id = Column(Integer, primary_key=True, index=True)
    dispute_id = Column(Integer, ForeignKey("disputes.id"), nullable=False)
    reason = Column(Text, nullable=False)
    priority = Column(String(32), default="MEDIUM")  # LOW, MEDIUM, HIGH, CRITICAL
    assigned_to = Column(String(100), nullable=True)
    sla_deadline = Column(DateTime, nullable=True)
    status = Column(String(32), default="OPEN")  # OPEN, RESOLVED, REJECTED
    resolution_note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    resolved_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
