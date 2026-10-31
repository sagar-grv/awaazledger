"""Deterministic risk evaluation engine for UPI dispute resolution."""

from typing import Dict, Any, List


class RiskEngine:
    """Evaluates multi-factor risk scores and fraud signals from reconciliation data."""

    def evaluate(self, reconciliation: Dict[str, Any]) -> Dict[str, Any]:
        """Calculates deterministic fraud score, operational risk score, and risk level."""
        fraud_score = 0.0
        risk_score = 0.0

        risk_signals = reconciliation.get("risk_signals", {})
        policy_inputs = reconciliation.get("policy_inputs", {})

        invalid_utr = reconciliation.get("invalid_utr", False)
        user_mismatch = reconciliation.get("user_mismatch", False)
        duplicate_debit = reconciliation.get("duplicate_debit", False)
        ghost_success = reconciliation.get("ghost_success", False)
        amount_mismatch = reconciliation.get("amount_mismatch", False)

        blacklisted = risk_signals.get("blacklisted", False)
        velocity_flag = risk_signals.get("velocity_flag", False)
        trust_score = risk_signals.get("trust_score", 100)
        low_trust = risk_signals.get("low_trust", False)
        rbi_tat_breach_candidate = policy_inputs.get("rbi_tat_breach_candidate", False)

        # Severe amount mismatch check (> INR 100 and > 10%)
        cbs_amount = reconciliation.get("cbs_amount")
        claimed_amount = reconciliation.get("claimed_amount")
        severe_amount_mismatch = False
        if amount_mismatch and cbs_amount is not None and claimed_amount is not None:
            diff = abs(cbs_amount - claimed_amount)
            severe_amount_mismatch = diff > max(100.0, 0.10 * claimed_amount)

        # --- Compute Fraud Score ---
        if invalid_utr:
            fraud_score += 50.0
        if user_mismatch:
            fraud_score += 50.0
        if blacklisted:
            fraud_score += 50.0
        if severe_amount_mismatch:
            fraud_score += 50.0
        if trust_score < 40:
            fraud_score += 40.0
        if velocity_flag:
            fraud_score += 15.0
        if duplicate_debit:
            fraud_score += 10.0
        if amount_mismatch and not severe_amount_mismatch:
            fraud_score += 20.0

        # --- Compute Operational Risk Score ---
        if trust_score < 85:
            risk_score += 10.0
        if trust_score < 60:
            risk_score += 25.0
        if duplicate_debit:
            risk_score += 20.0
        if amount_mismatch:
            risk_score += 20.0
        if rbi_tat_breach_candidate:
            risk_score += 5.0
        if velocity_flag:
            risk_score += 15.0

        fraud_score = min(100.0, max(0.0, fraud_score))
        risk_score = min(100.0, max(0.0, risk_score))

        # --- Determine Risk Level ---
        if (
            fraud_score >= 50.0
            or blacklisted
            or invalid_utr
            or user_mismatch
            or severe_amount_mismatch
        ):
            risk_level = "CRITICAL"
        elif (
            risk_score >= 40.0
            or duplicate_debit
            or amount_mismatch
            or trust_score < 60
        ):
            risk_level = "HIGH"
        elif (
            risk_score >= 20.0
            or trust_score < 85
            or rbi_tat_breach_candidate
        ):
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        # --- Generate Diagnostic Reasons ---
        reasons: List[str] = []
        if invalid_utr:
            reasons.append("Invalid or untraceable UTR record on switch")
        if user_mismatch:
            reasons.append("Transaction account does not match claiming user ID")
        if blacklisted:
            reasons.append("User is flagged on internal risk blacklist")
        if severe_amount_mismatch:
            reasons.append(f"Severe amount discrepancy: Claimed INR {claimed_amount} vs Bank Debit INR {cbs_amount}")
        elif amount_mismatch:
            reasons.append("Minor amount mismatch between claim and banking ledger")
        if duplicate_debit:
            reasons.append("Duplicate payment debit detected within time window")
        if velocity_flag:
            reasons.append("High dispute velocity in user history")
        if rbi_tat_breach_candidate:
            reasons.append("Transaction has breached RBI TAT resolution turnaround")
        if not reasons:
            reasons.append("User trust score is high")
            reasons.append("No duplicate debit detected")
            reasons.append("No invalid UTR detected")

        signals = {
            "invalid_utr": invalid_utr,
            "user_mismatch": user_mismatch,
            "blacklisted": blacklisted,
            "severe_amount_mismatch": severe_amount_mismatch,
            "amount_mismatch": amount_mismatch,
            "duplicate_debit": duplicate_debit,
            "ghost_success": ghost_success,
            "velocity_flag": velocity_flag,
            "low_trust": low_trust,
            "rbi_tat_breach_candidate": rbi_tat_breach_candidate,
        }

        return {
            "fraud_score": fraud_score,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "signals": signals,
            "reasons": reasons,
        }
