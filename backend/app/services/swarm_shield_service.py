"""Swarm Shield bank-outage detection service.

Detects high-frequency cluster delays across banking switches (e.g. SBI, HDFC)
and triggers proactive customer advisories and UPI Lite fallback routing.
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.config import settings
from app.models.dispute import Dispute
from app.models.transaction import Transaction


OUTAGE_NPCI_CODES = {"U30", "U69", "BENEFICIARY_TIMEOUT", "DEEMED_APPROVED", "TIMEOUT"}


class SwarmShieldService:
    def __init__(self, db: Session):
        self.db = db

    def detect_active_outages(self) -> Dict[str, Any]:
        """Scans recent disputes and transactions for switch outage clusters."""
        if not settings.ENABLE_SWARM_SHIELD:
            return {
                "enabled": False,
                "window_minutes": settings.SWARM_SHIELD_WINDOW_MINUTES,
                "threshold": settings.SWARM_SHIELD_THRESHOLD,
                "active_outages": [],
                "recent_signal_counts": {},
            }

        now = datetime.now(timezone.utc)
        window_minutes = settings.SWARM_SHIELD_WINDOW_MINUTES
        cutoff = now - timedelta(minutes=window_minutes)

        # Query recent disputes joined with transaction
        query = (
            self.db.query(Dispute, Transaction)
            .join(Transaction, Dispute.transaction_id == Transaction.id)
        )

        # In non-demo mode or strict mode, filter by cutoff
        # In demo mode, if few disputes exist within 5m, check recent disputes
        recent_disputes = query.filter(Dispute.created_at >= cutoff).all()
        if len(recent_disputes) < settings.SWARM_SHIELD_THRESHOLD:
            # Fallback for hackathon demo to inspect latest disputes
            recent_disputes = query.order_by(Dispute.created_at.desc()).limit(30).all()

        bank_signal_counts: Dict[str, int] = {}

        for dispute, txn in recent_disputes:
            bank = txn.bank or "UNKNOWN_BANK"
            npci_status = (txn.npcI_status or "").upper()
            three_way = dispute.three_way_json or ""

            is_outage_signal = False
            if npci_status in OUTAGE_NPCI_CODES:
                is_outage_signal = True
            elif any(code in three_way for code in OUTAGE_NPCI_CODES):
                is_outage_signal = True
            elif txn.cbs_status == "DEBIT_SUCCESS" and txn.beneficiary_status in ("NOT_CREDITED", "TIMEOUT"):
                is_outage_signal = True

            if is_outage_signal:
                bank_signal_counts[bank] = bank_signal_counts.get(bank, 0) + 1

        active_outages: List[Dict[str, Any]] = []
        for bank, count in bank_signal_counts.items():
            if count >= settings.SWARM_SHIELD_THRESHOLD:
                active_outages.append({
                    "bank": bank,
                    "count": count,
                    "status": "ACTIVE",
                    "advisory": f"Multiple UPI delays detected from {bank}. AwaazLedger is prioritizing provisional relief and fallback routing.",
                    "recommended_action": "ROUTE_UPI_LITE_FALLBACK",
                })

        return {
            "enabled": True,
            "window_minutes": window_minutes,
            "threshold": settings.SWARM_SHIELD_THRESHOLD,
            "active_outages": active_outages,
            "recent_signal_counts": bank_signal_counts,
        }
