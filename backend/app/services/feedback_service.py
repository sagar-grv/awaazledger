"""Customer feedback parsing, pending state tracking, and escalation routing service."""

import re
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.config import settings
from app.models.feedback import Feedback
from app.models.dispute import Dispute
from app.models.user import User
from app.models.escalation import Escalation
from app.models.audit_log import AuditLog
from app.schemas.feedback import FeedbackSummary, FeedbackCreate
from app.services.channel_identity_service import normalize_phone_number

# In-memory tracking for pending feedback prompts keyed by normalized phone
# Structure: {phone: {"dispute_id": int, "expires_at": datetime}}
_PENDING_FEEDBACK: Dict[str, Dict[str, Any]] = {}


def hash_phone(phone: str) -> str:
    """Returns SHA256 hash of normalized phone number for privacy."""
    norm = normalize_phone_number(phone)
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()[:16]


class FeedbackService:
    def __init__(self, db: Session):
        self.db = db

    def parse_whatsapp_feedback(self, text: str) -> Optional[str]:
        """Maps user's incoming response string to a structured feedback rating."""
        if not text:
            return None

        # If message contains a 12-digit UTR or is a long message, it is a complaint, not a feedback rating
        if re.search(r"\b\d{12}\b", text):
            return None

        cleaned = re.sub(r"[^\w\s]", " ", text.lower()).strip()
        tokens = set(cleaned.split())

        # Only evaluate concise messages (<= 6 words) as feedback ratings
        if len(cleaned.split()) > 6:
            return None

        # 1. Wrong Decision
        if "4" in tokens or "wrong" in cleaned or "galat" in tokens or "incorrect" in tokens or "disagree" in tokens:
            return "WRONG_DECISION"

        # 2. Talk to human
        if "3" in tokens or "human" in tokens or "agent" in tokens or "operator" in tokens or "executive" in tokens:
            return "HUMAN_REQUEST"

        # 3. Not Helpful (evaluated before generic helpful)
        if (
            "2" in tokens
            or "not helpful" in cleaned
            or "nothelpful" in tokens
            or "unhelpful" in tokens
            or "bad" in tokens
            or "bekar" in tokens
            or "nahi" in tokens
            or "no" in tokens
        ):
            return "NOT_HELPFUL"

        # 4. Helpful
        if (
            "1" in tokens
            or "helpful" in tokens
            or "sahi" in tokens
            or "good" in tokens
            or "satisfied" in tokens
            or cleaned in ("yes", "haan", "theek", "thek")
            or "sahi" in cleaned
        ):
            return "HELPFUL"

        return None

    def register_pending_feedback(self, phone: str, dispute_id: int):
        """Registers a pending feedback expectation for an active user phone."""
        norm_phone = normalize_phone_number(phone)
        expiry_minutes = getattr(settings, "FEEDBACK_EXPIRY_MINUTES", 30)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=expiry_minutes)
        _PENDING_FEEDBACK[norm_phone] = {
            "dispute_id": dispute_id,
            "expires_at": expires_at,
        }

    def has_pending_feedback(self, phone: str) -> bool:
        """Checks if there is an active pending feedback prompt for this phone."""
        norm_phone = normalize_phone_number(phone)
        entry = _PENDING_FEEDBACK.get(norm_phone)
        if not entry:
            return False
        if datetime.now(timezone.utc) > entry["expires_at"]:
            _PENDING_FEEDBACK.pop(norm_phone, None)
            return False
        return True

    def consume_feedback(self, phone: str, text: str) -> Optional[Feedback]:
        """Consumes a pending feedback response if valid, executing required human escalations."""
        rating = self.parse_whatsapp_feedback(text)
        if not rating:
            return None

        norm_phone = normalize_phone_number(phone)
        entry = _PENDING_FEEDBACK.pop(norm_phone, None)
        dispute_id = entry["dispute_id"] if entry else None

        # Fallback: if not in memory, find the latest dispute for this user
        if not dispute_id:
            from app.services.channel_identity_service import resolve_user_by_phone
            user_info = resolve_user_by_phone(norm_phone)
            if user_info:
                latest_disp = (
                    self.db.query(Dispute)
                    .filter(Dispute.user_id == user_info["user_id"])
                    .order_by(Dispute.created_at.desc())
                    .first()
                )
                if latest_disp:
                    dispute_id = latest_disp.id

        user_id = None
        dispute = None
        if dispute_id:
            dispute = self.db.query(Dispute).filter(Dispute.id == dispute_id).first()
            if dispute:
                user_id = dispute.user_id

        # 1. Create Feedback record
        fb = Feedback(
            dispute_id=dispute_id,
            user_id=user_id,
            phone_hash=hash_phone(norm_phone),
            rating=rating,
            comment=text.strip(),
            source="WHATSAPP",
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(fb)

        # 2. Handle side-effects for HUMAN_REQUEST and WRONG_DECISION
        if dispute:
            now = datetime.now(timezone.utc)
            if rating == "HUMAN_REQUEST":
                # Create or update escalation
                existing_esc = self.db.query(Escalation).filter(Escalation.dispute_id == dispute.id).first()
                if not existing_esc:
                    sla_deadline = now + timedelta(minutes=15)
                    esc = Escalation(
                        dispute_id=dispute.id,
                        reason="CUSTOMER_REQUESTED_HUMAN_SUPPORT",
                        priority="HIGH",
                        sla_deadline=sla_deadline,
                        status="OPEN",
                        created_at=now,
                    )
                    self.db.add(esc)
                else:
                    existing_esc.reason = "CUSTOMER_REQUESTED_HUMAN_SUPPORT"
                    existing_esc.status = "OPEN"

                dispute.status = "ESCALATED"
                audit = AuditLog(
                    dispute_id=dispute.id,
                    actor="CUSTOMER",
                    event="CUSTOMER_REQUESTED_HUMAN_SPECIALIST",
                    output_status="SUCCESS",
                    timestamp=now,
                )
                self.db.add(audit)

            elif rating == "WRONG_DECISION":
                # Create review escalation
                existing_esc = self.db.query(Escalation).filter(Escalation.dispute_id == dispute.id).first()
                if not existing_esc:
                    sla_deadline = now + timedelta(minutes=10)
                    esc = Escalation(
                        dispute_id=dispute.id,
                        reason="CUSTOMER_CONTESTED_DECISION_QUALITY_REVIEW",
                        priority="CRITICAL",
                        sla_deadline=sla_deadline,
                        status="OPEN",
                        created_at=now,
                    )
                    self.db.add(esc)

                audit = AuditLog(
                    dispute_id=dispute.id,
                    actor="CUSTOMER",
                    event="FEEDBACK_WRONG_DECISION_CONTESTED",
                    output_status="SUCCESS",
                    timestamp=now,
                )
                self.db.add(audit)

        self.db.commit()
        self.db.refresh(fb)
        return fb

    def get_summary(self) -> FeedbackSummary:
        """Returns aggregated feedback metrics and customer satisfaction percentage."""
        feedbacks = self.db.query(Feedback).all()
        total = len(feedbacks)
        helpful = sum(1 for f in feedbacks if f.rating == "HELPFUL")
        not_helpful = sum(1 for f in feedbacks if f.rating == "NOT_HELPFUL")
        human_req = sum(1 for f in feedbacks if f.rating == "HUMAN_REQUEST")
        wrong_dec = sum(1 for f in feedbacks if f.rating == "WRONG_DECISION")

        csat = (helpful / total * 100.0) if total > 0 else 100.0

        # Count active pending feedback
        now = datetime.now(timezone.utc)
        active_pending = sum(
            1 for entry in _PENDING_FEEDBACK.values() if entry.get("expires_at", now) > now
        )

        return FeedbackSummary(
            total_feedback=total,
            helpful_count=helpful,
            not_helpful_count=not_helpful,
            human_request_count=human_req,
            wrong_decision_count=wrong_dec,
            customer_satisfaction_pct=round(csat, 1),
            pending_feedback_count=active_pending,
        )
