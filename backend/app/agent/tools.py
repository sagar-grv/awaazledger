"""Agent tool definitions for ledger and network lookups."""

from typing import Dict, Any


def query_bank_cbs(account_number: str, date_str: str) -> Dict[str, Any]:
    """Queries Core Banking System for account debits."""
    return {
        "status": "SUCCESS",
        "account": account_number,
        "date": date_str,
        "debit_confirmed": True,
        "balance_deducted": True,
    }


def query_npci_udir(utr: str) -> Dict[str, Any]:
    """Queries NPCI Unified Dispute and Issue Resolution (UDIR) gateway."""
    return {
        "status": "SUCCESS",
        "utr": utr,
        "npci_response_code": "00",
        "settlement_status": "PENDING_AT_BENEFICIARY",
        "beneficiary_bank_code": "HDFC0000001",
    }


def query_paytm_ledger(utr: str) -> Dict[str, Any]:
    """Queries internal Paytm payments ledger for gateway state."""
    return {
        "status": "SUCCESS",
        "utr": utr,
        "internal_status": "TIMEOUT_SENT_TO_NPCI",
        "timestamp": "2026-10-30T10:15:30Z",
    }


def fetch_user_trust(user_id: int) -> Dict[str, Any]:
    """Retrieves user trust profile and historical resolution score."""
    return {
        "user_id": user_id,
        "trust_score": 92,
        "dispute_history_count": 1,
        "verified_account": True,
    }
