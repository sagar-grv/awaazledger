"""Merchant sale recovery service.

Generates immediate checkout recovery QR codes and collect links when a customer's
payment is held in banking transit, preventing lost in-store sales and cart abandonment.
"""

import json
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.dispute import Dispute
from app.models.action import Action
from app.models.audit_log import AuditLog
from app.schemas.dispute import ActionType


class MerchantRecoveryService:
    def __init__(self, db: Session):
        self.db = db

    def generate_recovery_payload(self, dispute_id: int) -> Dict[str, Any]:
        """Generates or retrieves a secure merchant sale recovery link for a dispute."""
        if not settings.ENABLE_MERCHANT_RECOVERY:
            return {
                "status": "DISABLED",
                "message": "Merchant recovery is disabled in this environment.",
            }

        dispute = self.db.query(Dispute).filter(Dispute.id == dispute_id).first()
        if not dispute:
            raise ValueError(f"Dispute #{dispute_id} not found")

        # Ineligible checks
        if dispute.status == "FRAUD_BLOCKED" or dispute.agent_decision in ("FRAUD_BLOCK", "MANUALLY_BLOCKED_FRAUD"):
            return {
                "status": "NOT_ELIGIBLE",
                "message": "Dispute is blocked due to risk verification policies.",
            }

        if dispute.agent_decision == "GHOST_SUCCESS_RECEIPT" or dispute.status == "RECEIPT_GENERATED":
            return {
                "status": "RECEIPT_ALREADY_AVAILABLE",
                "message": "Merchant has already been credited. Digital receipt is available to cashier.",
            }

        # Idempotency check: return cached recovery if already created
        existing_action = (
            self.db.query(Action)
            .filter(
                Action.dispute_id == dispute.id,
                Action.action_type == ActionType.MERCHANT_RECOVERY_LINK.value,
            )
            .first()
        )
        if existing_action and existing_action.payload_json:
            try:
                return json.loads(existing_action.payload_json)
            except Exception:
                pass

        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=15)
        recovery_id = f"MR-{dispute.dispute_code}"

        payload = {
            "dispute_code": dispute.dispute_code,
            "merchant_recovery_id": recovery_id,
            "status": "RECOVERY_LINK_GENERATED",
            "qr_url": f"https://paytm.example/qr/{recovery_id}",
            "collect_link": f"https://paytm.example/collect/{recovery_id}",
            "fallback_options": [
                "Paytm UPI Lite",
                "Wallet fallback",
                "Retry after original reversal",
            ],
            "merchant_message": "Customer payment is pending. Share this recovery QR/link to complete sale safely.",
            "customer_message": "AwaazLedger has created a secure recovery link so you can complete your purchase without paying twice.",
            "expires_at": expires_at.isoformat(),
        }

        # Record Action
        act = Action(
            dispute_id=dispute.id,
            action_type=ActionType.MERCHANT_RECOVERY_LINK.value,
            executed_by="AI_TEAMMATE",
            payload_json=json.dumps(payload),
            status="COMPLETED",
            created_at=now,
        )
        self.db.add(act)

        # Record AuditLog
        audit = AuditLog(
            dispute_id=dispute.id,
            actor="AI_TEAMMATE",
            event="MERCHANT_RECOVERY_GENERATED",
            output_status="SUCCESS",
            details_json=json.dumps(payload),
            timestamp=now,
        )
        self.db.add(audit)

        self.db.commit()

        return payload
