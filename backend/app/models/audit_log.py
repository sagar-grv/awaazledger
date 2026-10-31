"""AuditLog database model."""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from app.db.base import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    dispute_id = Column(Integer, ForeignKey("disputes.id"), nullable=False)
    actor = Column(String(64), default="AGENT_STATE_MACHINE")
    event = Column(String(64), nullable=False)
    input_hash = Column(String(64), nullable=True)
    output_status = Column(String(32), nullable=True)
    details_json = Column(Text, nullable=True)
    consent_id = Column(Integer, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
