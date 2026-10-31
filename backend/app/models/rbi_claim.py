"""RbiClaim database model."""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from app.db.base import Base


class RbiClaim(Base):
    __tablename__ = "rbi_claims"

    id = Column(Integer, primary_key=True, index=True)
    dispute_id = Column(Integer, ForeignKey("disputes.id"), nullable=False)
    claim_amount = Column(Float, default=0.0)
    delay_days = Column(Integer, default=0)
    status = Column(String(32), default="FILED")  # FILED, SETTLED, REJECTED
    filed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    settled_at = Column(DateTime, nullable=True)
    responsible_entity = Column(String(64), default="REMITTER_BANK")
