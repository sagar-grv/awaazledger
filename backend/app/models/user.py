"""User database model."""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    mobile_hash = Column(String(64), unique=True, index=True, nullable=False)
    paytm_id = Column(String(100), unique=True, index=True, nullable=False)
    language = Column(String(10), default="hi")  # hi, en, mr, etc.
    trust_score = Column(Integer, default=100)   # 0 to 100
    kyc_status = Column(String(20), default="VERIFIED")  # VERIFIED, PENDING, FAILED
    device_id = Column(String(64), nullable=True)
    blacklisted = Column(Boolean, default=False)
    previous_dispute_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
