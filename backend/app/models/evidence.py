"""Evidence database model."""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey
from app.db.base import Base


class Evidence(Base):
    __tablename__ = "evidences"

    id = Column(Integer, primary_key=True, index=True)
    dispute_id = Column(Integer, ForeignKey("disputes.id"), nullable=False)
    type = Column(String(32), nullable=False)  # VOICE, SCREENSHOT, TEXT
    url_or_path = Column(String(255), nullable=True)
    sha256 = Column(String(64), nullable=True)
    ocr_json = Column(Text, nullable=True)
    confidence = Column(Float, default=1.0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
