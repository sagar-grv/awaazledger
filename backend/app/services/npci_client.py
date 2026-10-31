"""NPCI UDIR (Unified Dispute and Issue Resolution) mock client."""

from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.transaction import Transaction


class NPCIClient:
    """Deterministic mock for NPCI UPI Switch and UDIR gateway."""

    def __init__(self, db: Optional[Session] = None):
        self._db = db

    def _get_db(self) -> Session:
        return self._db or SessionLocal()

    def query_npci_udir(self, utr: str) -> Dict[str, Any]:
        """Queries NPCI switch for transaction and settlement state."""
        db = self._get_db()
        should_close = self._db is None
        try:
            txn = db.query(Transaction).filter(Transaction.utr == utr).first()
            if not txn:
                return {
                    "utr": utr,
                    "found": False,
                    "npcI_status": "INVALID_UTR",
                    "state": "INVALID",
                    "failure_point": "INVALID_UTR",
                    "beneficiary_bank": None,
                    "merchant_id": None,
                    "amount": None,
                    "beneficiary_credited": False,
                    "auto_reversal_scheduled": False,
                    "expected_reversal_time": None,
                }

            npcI_status = txn.npcI_status or "U30"
            beneficiary_status = txn.beneficiary_status or "NOT_CREDITED"
            beneficiary_credited = (beneficiary_status == "CREDITED") or (npcI_status == "SUCCESS")

            # Determine failure point
            if npcI_status == "SUCCESS":
                if txn.status == "PENDING":
                    failure_point = "BENEFICIARY_CREDITED_BUT_DISPLAY_PENDING"
                else:
                    failure_point = "NONE"
            elif npcI_status in ["U30", "BENEFICIARY_TIMEOUT", "DEEMED_APPROVED"]:
                failure_point = "BENEFICIARY_BANK_TIMEOUT"
            elif npcI_status == "U69":
                failure_point = "SWITCH_LATENCY"
            elif npcI_status == "INVALID_UTR":
                failure_point = "INVALID_UTR"
            else:
                failure_point = "REMITTER_BANK_TIMEOUT"

            # Auto-reversal scheduled for hanging/timed-out transactions
            auto_reversal_scheduled = (
                not beneficiary_credited
                and npcI_status in ["U30", "U69", "BENEFICIARY_TIMEOUT", "DEEMED_APPROVED"]
            )

            state_desc = "SUCCESS" if npcI_status == "SUCCESS" else ("DEEMED_APPROVED" if npcI_status == "U30" else npcI_status)

            return {
                "utr": txn.utr,
                "found": True,
                "npcI_status": npcI_status,
                "state": state_desc,
                "failure_point": failure_point,
                "beneficiary_bank": txn.bank or "ICICI",
                "merchant_id": txn.merchant_id,
                "amount": txn.amount,
                "beneficiary_credited": beneficiary_credited,
                "auto_reversal_scheduled": auto_reversal_scheduled,
                "expected_reversal_time": "T+1" if auto_reversal_scheduled else None,
            }
        finally:
            if should_close:
                db.close()


async def query_npci_udir(utr: str) -> Dict[str, Any]:
    """Async convenience wrapper for NPCIClient."""
    return NPCIClient().query_npci_udir(utr=utr)
