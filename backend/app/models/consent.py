"""Consent database model."""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from app.db.base import Base


class Consent(Base):
    __tablename__ = "consents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    scopes = Column(String(255), default="DISPUTE_RESOLUTION,CBS_INQUIRY,NPCI_UDIR")
    channel = Column(String(32), default="SIMULATOR")
    granted_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    revoked_at = Column(DateTime, nullable=True)
