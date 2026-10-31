"""Core Banking System (CBS) mock client."""

from typing import Dict, Any, Optional
from datetime import timezone
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.transaction import Transaction


class CBSClient:
    """Deterministic mock for Remitter / Beneficiary Core Banking Systems."""

    def __init__(self, db: Optional[Session] = None):
        self._db = db

    def _get_db(self) -> Session:
        return self._db or SessionLocal()

    def query_bank_cbs(self, utr: str, user_id: Optional[int] = None) -> Dict[str, Any]:
        """Queries Core Banking System for debit verification by UTR."""
        db = self._get_db()
        should_close = self._db is None
        try:
            txn = db.query(Transaction).filter(Transaction.utr == utr).first()
            if not txn:
                return {
                    "utr": utr,
                    "found": False,
                    "identity_match": False,
                    "cbs_status": "UNKNOWN",
                    "amount": None,
                    "currency": None,
                    "bank": None,
                    "merchant_id": None,
                    "merchant_name": None,
                    "debited_at": None,
                    "reversal_status": None,
                    "user_id": None,
                }

            identity_match = (user_id is None) or (txn.user_id == user_id)
            debited_at_str = txn.debited_at.isoformat() if txn.debited_at else None

            return {
                "utr": txn.utr,
                "found": True,
                "identity_match": identity_match,
                "cbs_status": txn.cbs_status or "DEBIT_SUCCESS",
                "amount": txn.amount,
                "currency": txn.currency or "INR",
                "bank": txn.bank or "UNKNOWN",
                "merchant_id": txn.merchant_id,
                "merchant_name": txn.merchant_name,
                "debited_at": debited_at_str,
                "reversal_status": txn.reversal_status or "NONE",
                "user_id": txn.user_id,
            }
        finally:
            if should_close:
                db.close()


async def query_bank_cbs(utr: str, user_id: Optional[int] = None) -> Dict[str, Any]:
    """Async convenience wrapper for CBSClient."""
    return CBSClient().query_bank_cbs(utr=utr, user_id=user_id)
