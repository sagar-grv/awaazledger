"""SQLAlchemy model for autonomous agent continuous learning and self-improvement telemetry."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from app.db.base import Base


class AgentLearningEntry(Base):
    __tablename__ = "agent_learning_entries"

    id = Column(Integer, primary_key=True, index=True)
    dispute_code = Column(String(50), nullable=True, index=True)
    trigger_type = Column(String(50), nullable=False)  # FEEDBACK_HELPFUL, FEEDBACK_CORRECTION, HUMAN_OVERRIDE, AUTONOMOUS_SETTLEMENT
    input_modality = Column(String(20), default="TEXT")  # TEXT, VOICE, IMAGE
    language = Column(String(10), default="hi")
    intent = Column(String(50), nullable=True)
    confidence_score = Column(Float, default=0.85)
    adaptation_summary = Column(String(255), nullable=False)
    learning_payload = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
