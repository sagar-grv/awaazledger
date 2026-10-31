"""Consent stub service for hackathon dispute resolution."""

from typing import Dict, Any, List
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
import json
from app.models.consent import Consent

DEFAULT_SCOPES = [
    "transaction_read",
    "bridge_credit",
    "rbi_claim",
    "human_escalation",
    "fraud_review",
]


class ConsentService:
    """Deterministic consent manager verifying and recording user authorization."""

    @staticmethod
    def ensure_consent_sync(
        db: Session,
        user_id: int,
        channel: str = "SIMULATOR",
        scopes: List[str] = DEFAULT_SCOPES,
    ) -> Dict[str, Any]:
        """Finds active recent consent or creates a new consent record."""
        # Check if active consent exists within past 24 hours
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        existing = (
            db.query(Consent)
            .filter(
                Consent.user_id == user_id,
                Consent.channel == channel,
                Consent.granted_at >= cutoff,
                Consent.revoked_at.is_(None),
            )
            .first()
        )

        if existing:
            return {
                "consent_id": existing.id,
                "user_id": existing.user_id,
                "scopes": json.loads(existing.scopes) if existing.scopes.startswith("[") else existing.scopes.split(","),
                "channel": existing.channel,
                "granted_at": existing.granted_at.isoformat() if existing.granted_at else "",
                "reused": True,
            }

        # Create new consent record
        new_consent = Consent(
            user_id=user_id,
            scopes=json.dumps(scopes),
            channel=channel,
            granted_at=datetime.now(timezone.utc),
        )
        db.add(new_consent)
        db.commit()
        db.refresh(new_consent)

        return {
            "consent_id": new_consent.id,
            "user_id": new_consent.user_id,
            "scopes": scopes,
            "channel": new_consent.channel,
            "granted_at": new_consent.granted_at.isoformat() if new_consent.granted_at else "",
            "reused": False,
        }


async def ensure_consent(
    db: Session,
    user_id: int,
    channel: str = "SIMULATOR",
) -> Dict[str, Any]:
    """Async wrapper for consent provisioning."""
    return ConsentService.ensure_consent_sync(db=db, user_id=user_id, channel=channel)
