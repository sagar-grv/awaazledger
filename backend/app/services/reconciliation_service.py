"""Deterministic three-way reconciliation service across Bank CBS, NPCI UDIR, and Paytm Ledger."""

from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.core.config import settings
from app.models.transaction import Transaction
from app.services.cbs_client import CBSClient
from app.services.npci_client import NPCIClient
from app.services.paytm_ledger_client import PaytmLedgerClient
from app.services.trust_service import TrustService


class ReconciliationService:
    """Performs deterministic 3-way check and generates immutable facts and policy inputs."""

    def __init__(
        self,
        db: Optional[Session] = None,
        cbs_client: Optional[CBSClient] = None,
        npci_client: Optional[NPCIClient] = None,
        paytm_client: Optional[PaytmLedgerClient] = None,
        trust_service: Optional[TrustService] = None,
    ):
        self._db = db
        self.cbs_client = cbs_client or CBSClient(db=db)
        self.npci_client = npci_client or NPCIClient(db=db)
        self.paytm_client = paytm_client or PaytmLedgerClient(db=db)
        self.trust_service = trust_service or TrustService(db=db)

    def _get_db(self) -> Session:
        return self._db or SessionLocal()

    def check_duplicate_debit(
        self,
        user_id: int,
        utr: str,
        amount: Optional[float],
        merchant_id: Optional[str],
        debited_at: Optional[datetime],
        window_seconds: int = settings.DUPLICATE_WINDOW_SECONDS,
    ) -> List[str]:
        """Detects other debits to same merchant for same amount within window."""
        if not amount or not debited_at:
            return []

        db = self._get_db()
        should_close = self._db is None
        try:
            query = db.query(Transaction).filter(
                Transaction.user_id == user_id,
                Transaction.utr != utr,
            )
            if merchant_id:
                query = query.filter(Transaction.merchant_id == merchant_id)

            candidates = query.all()
            duplicate_utrs = []

            for candidate in candidates:
                # Compare amounts with small tolerance
                if abs(candidate.amount - amount) <= 1.0:
                    cand_time = candidate.debited_at or candidate.created_at
                    if cand_time:
                        # Normalize timezones for comparison
                        t1 = debited_at if debited_at.tzinfo else debited_at.replace(tzinfo=timezone.utc)
                        t2 = cand_time if cand_time.tzinfo else cand_time.replace(tzinfo=timezone.utc)
                        diff_sec = abs((t1 - t2).total_seconds())
                        if diff_sec <= window_seconds:
                            duplicate_utrs.append(candidate.utr)

            return duplicate_utrs
        finally:
            if should_close:
                db.close()

    def reconcile(
        self,
        utr: str,
        user_id: int,
        claimed_amount: Optional[float] = None,
        channel: str = "SIMULATOR",
    ) -> Dict[str, Any]:
        """Core deterministic 3-way reconciliation engine."""
        db = self._get_db()
        should_close = self._db is None
        try:
            # 1. Fetch raw facts from all 4 providers
            cbs_data = self.cbs_client.query_bank_cbs(utr=utr, user_id=user_id)
            npci_data = self.npci_client.query_npci_udir(utr=utr)
            paytm_data = self.paytm_client.query_paytm_ledger(utr=utr)
            trust_data = self.trust_service.get_user_trust(user_id=user_id)

            # 2. Extract and correlate signals
            cbs_found = cbs_data.get("found", False)
            cbs_debited = cbs_data.get("cbs_status") == "DEBIT_SUCCESS"
            cbs_amount = cbs_data.get("amount")
            npcI_found = npci_data.get("found", False)
            npcI_status = npci_data.get("npcI_status")
            failure_point = npci_data.get("failure_point")
            beneficiary_credited = npci_data.get("beneficiary_credited", False)
            merchant_credit_status = paytm_data.get("merchant_credit_status")
            paytm_settlement_status = paytm_data.get("settlement_status")
            auto_reversal_scheduled = (
                npci_data.get("auto_reversal_scheduled", False)
                or paytm_data.get("auto_reversal_scheduled", False)
            )

            # 3. Detect Invalid UTR & User Mismatch
            invalid_utr = (not cbs_found) or (not npcI_found) or (npcI_status == "INVALID_UTR")
            identity_match = cbs_data.get("identity_match", False) if cbs_found else False
            user_mismatch = bool(cbs_found and not identity_match)

            # 4. Amount Matching
            effective_claimed_amount = claimed_amount if claimed_amount is not None else cbs_amount
            amount_matches = True
            amount_mismatch = False
            severe_amount_mismatch = False

            if cbs_amount is not None and effective_claimed_amount is not None:
                diff = abs(cbs_amount - effective_claimed_amount)
                if diff > 1.0:
                    amount_mismatch = True
                    amount_matches = False
                    # Severe if difference exceeds max(100 INR, 10% of claimed amount)
                    severity_threshold = max(100.0, 0.10 * effective_claimed_amount)
                    severe_amount_mismatch = diff > severity_threshold

            # 5. Ghost Success Detection
            ghost_success = bool(cbs_debited and beneficiary_credited)

            # 6. Duplicate Debit Detection
            txn = db.query(Transaction).filter(Transaction.utr == utr).first() if not invalid_utr else None
            debited_at_val = txn.debited_at if txn else None
            merchant_id_val = txn.merchant_id if txn else None

            duplicate_utrs = self.check_duplicate_debit(
                user_id=user_id,
                utr=utr,
                amount=cbs_amount or effective_claimed_amount,
                merchant_id=merchant_id_val,
                debited_at=debited_at_val,
            )
            duplicate_debit = len(duplicate_utrs) > 0

            # 7. RBI TAT SLA Breach Detection
            rbi_tat_breach_candidate = False
            rbi_compensation_signal = False
            delay_days = 0

            if cbs_debited and not beneficiary_credited and debited_at_val:
                now_utc = datetime.now(timezone.utc)
                d_time = debited_at_val if debited_at_val.tzinfo else debited_at_val.replace(tzinfo=timezone.utc)
                elapsed_days = (now_utc - d_time).days
                allowed_tat_days = getattr(settings, "RBI_TAT_ALLOWED_DAYS", 1)
                if elapsed_days > allowed_tat_days:
                    delay_days = max(1, elapsed_days - allowed_tat_days)
                    rbi_tat_breach_candidate = True
                    rbi_compensation_signal = True

            # 8. Compile Risk Signals
            risk_signals = {
                "low_trust": trust_data.get("risk_band") in ["HIGH", "CRITICAL"],
                "blacklisted": trust_data.get("blacklisted", False),
                "velocity_flag": trust_data.get("velocity_flag", False),
                "previous_dispute_count": trust_data.get("previous_dispute_count", 0),
                "trust_score": trust_data.get("trust_score", 0),
                "kyc_status": trust_data.get("kyc_status", "UNKNOWN"),
            }

            # 9. Synthesize Policy Inputs (Facts to feed downstream Policy Engine)
            reasons: List[str] = []
            eligible_bridge_credit = False
            requires_human_review = False
            fraud_block = False
            info_request = False

            if invalid_utr:
                fraud_block = True
                reasons.append("Invalid UTR: Transaction record not found across banking switch")
            elif user_mismatch:
                fraud_block = True
                reasons.append("Identity Mismatch: Transaction belongs to a different user account")
            elif risk_signals["blacklisted"] or risk_signals["trust_score"] < 40:
                fraud_block = True
                reasons.append(f"High risk profile: User trust score {risk_signals['trust_score']} is below acceptable threshold or blacklisted")
            elif severe_amount_mismatch:
                fraud_block = True
                reasons.append(f"Severe amount mismatch: Claimed INR {effective_claimed_amount} vs CBS Debit INR {cbs_amount}")
            elif amount_mismatch:
                requires_human_review = True
                reasons.append(f"Minor amount discrepancy: Claimed INR {effective_claimed_amount} vs CBS Debit INR {cbs_amount}")
            elif duplicate_debit:
                requires_human_review = True
                reasons.append(f"Duplicate debit pattern detected: Multiple charges within {settings.DUPLICATE_WINDOW_SECONDS}s")
            elif ghost_success:
                reasons.append("Merchant already received payment. Generate verified receipt instead of bridge credit.")
            elif cbs_amount and cbs_amount > settings.AUTO_CREDIT_CEILING:
                requires_human_review = True
                reasons.append(f"Transaction amount INR {cbs_amount} exceeds autonomous ceiling of INR {settings.AUTO_CREDIT_CEILING}")
            elif cbs_debited and not beneficiary_credited:
                if risk_signals["trust_score"] >= settings.MIN_TRUST_SCORE and not risk_signals["low_trust"]:
                    eligible_bridge_credit = True
                    reasons = [
                        "CBS debit confirmed",
                        "NPCI indicates beneficiary timeout",
                        "Merchant not credited",
                        "Amount matches claimed amount",
                        "User trust score is high",
                    ]
                else:
                    requires_human_review = True
                    reasons.append(f"Medium trust user score {risk_signals['trust_score']}: Manual review recommended")
            else:
                requires_human_review = True
                reasons.append("Complex transaction state requires human operator verification")

            if rbi_tat_breach_candidate:
                reasons.append(f"RBI TAT SLA breached by {delay_days} days. Eligible for INR {delay_days * 100} delay compensation")

            policy_inputs = {
                "eligible_for_automatic_bridge_credit_signal": eligible_bridge_credit,
                "requires_human_review_signal": requires_human_review,
                "fraud_block_signal": fraud_block,
                "info_request_signal": info_request,
                "rbi_tat_breach_candidate": rbi_tat_breach_candidate,
                "rbi_compensation_signal": rbi_compensation_signal,
                "delay_days": delay_days,
                "reasons": reasons,
            }

            return {
                "utr": utr,
                "user_id": user_id,
                "identity_match": identity_match,
                "cbs_found": cbs_found,
                "cbs_debited": cbs_debited,
                "cbs_amount": cbs_amount,
                "claimed_amount": effective_claimed_amount,
                "amount_matches": amount_matches,
                "amount_mismatch": amount_mismatch,
                "npcI_found": npcI_found,
                "npcI_status": npcI_status,
                "failure_point": failure_point,
                "beneficiary_credited": beneficiary_credited,
                "merchant_credit_status": merchant_credit_status,
                "paytm_settlement_status": paytm_settlement_status,
                "auto_reversal_scheduled": auto_reversal_scheduled,
                "ghost_success": ghost_success,
                "duplicate_debit": duplicate_debit,
                "duplicate_utrs": duplicate_utrs,
                "invalid_utr": invalid_utr,
                "user_mismatch": user_mismatch,
                "risk_signals": risk_signals,
                "policy_inputs": policy_inputs,
                "raw": {
                    "cbs": cbs_data,
                    "npcI": npci_data,
                    "paytm_ledger": paytm_data,
                    "trust": trust_data,
                },
            }
        finally:
            if should_close:
                db.close()


async def perform_three_way_check(
    utr: str,
    user_id: int,
    claimed_amount: Optional[float] = None,
    channel: str = "SIMULATOR",
) -> Dict[str, Any]:
    """Async convenience wrapper for three-way reconciliation."""
    return ReconciliationService().reconcile(
        utr=utr,
        user_id=user_id,
        claimed_amount=claimed_amount,
        channel=channel,
    )
