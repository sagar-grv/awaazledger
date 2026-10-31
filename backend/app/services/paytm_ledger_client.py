"""Paytm settlement and merchant ledger mock client."""

from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.transaction import Transaction


class PaytmLedgerClient:
    """Deterministic mock for Paytm internal payments and merchant settlement ledger."""

    def __init__(self, db: Optional[Session] = None):
        self._db = db

    def _get_db(self) -> Session:
        return self._db or SessionLocal()

    def query_paytm_ledger(self, utr: str) -> Dict[str, Any]:
        """Queries internal Paytm ledger for settlement and merchant credit status."""
        db = self._get_db()
        should_close = self._db is None
        try:
            txn = db.query(Transaction).filter(Transaction.utr == utr).first()
            if not txn:
                return {
                    "utr": utr,
                    "found": False,
                    "settlement_status": None,
                    "merchant_credit_status": None,
                    "soundbox_status": None,
                    "expected_reversal_time": None,
                    "auto_reversal_scheduled": False,
                }

            settlement_status = txn.settlement_status or "PENDING"
            beneficiary_status = txn.beneficiary_status or "NOT_CREDITED"

            # Check if merchant received funds
            is_merchant_credited = (
                settlement_status == "SETTLED"
                or beneficiary_status == "CREDITED"
                or txn.npcI_status == "SUCCESS"
            )

            merchant_credit_status = "MERCHANT_CREDITED" if is_merchant_credited else "NOT_CREDITED"
            soundbox_status = "CONFIRMED" if is_merchant_credited else "NO_CONFIRMATION"

            auto_reversal_scheduled = (
                not is_merchant_credited
                and settlement_status in ["PENDING", "IN_TRANSIT"]
            )

            return {
                "utr": txn.utr,
                "found": True,
                "settlement_status": settlement_status,
                "merchant_credit_status": merchant_credit_status,
                "soundbox_status": soundbox_status,
                "expected_reversal_time": "T+1" if auto_reversal_scheduled else None,
                "auto_reversal_scheduled": auto_reversal_scheduled,
            }
        finally:
            if should_close:
                db.close()


async def query_paytm_ledger(utr: str) -> Dict[str, Any]:
    """Async convenience wrapper for PaytmLedgerClient."""
    return PaytmLedgerClient().query_paytm_ledger(utr=utr)
