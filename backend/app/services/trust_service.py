"""User trust and reputation scoring service."""

from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.user import User


class TrustService:
    """Deterministic trust and risk profiling service based on user history."""

    def __init__(self, db: Optional[Session] = None):
        self._db = db

    def _get_db(self) -> Session:
        return self._db or SessionLocal()

    def get_user_trust(self, user_id: int) -> Dict[str, Any]:
        """Calculates deterministic trust profile and risk band for a user."""
        db = self._get_db()
        should_close = self._db is None
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {
                    "user_id": user_id,
                    "trust_score": 0,
                    "kyc_status": "UNKNOWN",
                    "blacklisted": True,
                    "device_consistent": False,
                    "previous_dispute_count": 0,
                    "risk_band": "CRITICAL",
                    "recent_dispute_count": 0,
                    "fraud_history_flag": True,
                    "velocity_flag": False,
                }

            trust_score = user.trust_score
            blacklisted = user.blacklisted or False
            prev_disputes = user.previous_dispute_count or 0

            # Determine risk band
            if blacklisted or trust_score < 40:
                risk_band = "CRITICAL"
            elif trust_score < 60:
                risk_band = "HIGH"
            elif trust_score < 85:
                risk_band = "MEDIUM"
            else:
                risk_band = "LOW"

            velocity_flag = prev_disputes >= 3
            fraud_history_flag = blacklisted or (trust_score < 50)

            return {
                "user_id": user.id,
                "trust_score": trust_score,
                "kyc_status": user.kyc_status or "VERIFIED",
                "blacklisted": blacklisted,
                "device_consistent": True,
                "previous_dispute_count": prev_disputes,
                "risk_band": risk_band,
                "recent_dispute_count": prev_disputes,
                "fraud_history_flag": fraud_history_flag,
                "velocity_flag": velocity_flag,
            }
        finally:
            if should_close:
                db.close()


async def fetch_user_trust(user_id: int) -> Dict[str, Any]:
    """Async convenience wrapper for TrustService."""
    return TrustService().get_user_trust(user_id=user_id)
