"""BridgeCredit database model."""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from app.db.base import Base


class BridgeCredit(Base):
    __tablename__ = "bridge_credits"

    id = Column(Integer, primary_key=True, index=True)
    dispute_id = Column(Integer, ForeignKey("disputes.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(String(32), default="ISSUED")  # ISSUED, RECOVERED, EXPIRED, FAILED
    issued_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    recovered_at = Column(DateTime, nullable=True)
    expiry_at = Column(DateTime, nullable=True)
    idempotency_key = Column(String(64), unique=True, nullable=True)
