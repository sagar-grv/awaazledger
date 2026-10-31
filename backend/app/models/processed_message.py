"""Processed WhatsApp message deduplication table for webhook idempotency."""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Text
from app.db.base import Base


class ProcessedMessage(Base):
    __tablename__ = "processed_messages"

    id = Column(Integer, primary_key=True, index=True)
    channel = Column(String(32), default="WHATSAPP_EVOLUTION")
    message_id = Column(String(128), unique=True, index=True, nullable=False)
    phone_hash = Column(String(64), nullable=True)
    status = Column(String(32), default="PROCESSED")  # PROCESSED, FAILED, DUPLICATE
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
