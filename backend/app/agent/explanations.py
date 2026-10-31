"""Deterministic customer and supervisor explanation generator."""

from typing import Dict, Any


def generate_explanations(
    decision: Dict[str, Any],
    reconciliation: Dict[str, Any],
    risk: Dict[str, Any],
    dispute: Dict[str, Any],
    user_language: str = "hi",
) -> Dict[str, str]:
    """Generates natural language explanations tailored for customer (vernacular) and internal auditor."""
    decision_val = decision.get("decision")
    decision_str = decision_val.value if hasattr(decision_val, "value") else str(decision_val)

    amount = dispute.get("amount") or reconciliation.get("cbs_amount") or 0.0
    dispute_code = dispute.get("dispute_code", "DISP-REF")
    receipt_id = f"RCPT-{dispute_code}"
    is_hi = (user_language or "hi").lower().startswith("hi")

    # --- Customer Vernacular Explanation ---
    if decision_str == "AUTO_RESOLVE":
        if reconciliation.get("ghost_success"):
            explanation_user = (
                f"Payment merchant ko mil chuka hai. Sirf aapke app mein status update nahi hua. "
                f"Verified digital receipt generate kar diya gaya hai: {receipt_id}."
                if is_hi
                else f"The merchant has already received payment. Only your app status was pending. A verified digital receipt has been generated: {receipt_id}."
            )
        else:
            explanation_user = (
                f"INR {amount:.2f} ka provisional bridge credit add kar diya gaya hai. "
                f"Aap merchant ko ye reference dikha sakte hain: {dispute_code}. "
                f"Original transaction reconcile hone tak RBI TAT timer active hai."
                if is_hi
                else f"INR {amount:.2f} provisional bridge credit has been added. You can show reference {dispute_code} to the merchant. RBI TAT timer is active until original transaction reconciles."
            )
    elif decision_str == "HUMAN_ESCALATE":
        explanation_user = (
            "Ye case high-value ya risky hai. Maine poora verified dossier human specialist ko bhej diya hai. Expected review: 15 minutes."
            if is_hi
            else "This case is high-value or risky. I have sent a complete verified dossier to a human specialist. Expected review: 15 minutes."
        )
    elif decision_str == "FRAUD_BLOCK":
        explanation_user = (
            "Transaction verify nahi ho paya. Security ke liye bridge credit block kar diya gaya hai aur risk team ko alert bheja gaya hai."
            if is_hi
            else "The transaction could not be verified. For security, bridge credit has been blocked and the risk team has been alerted."
        )
    elif decision_str == "INFO_REQUEST":
        explanation_user = (
            "Mujhe thodi aur detail chahiye. Kripya clear screenshot ya 12-digit UTR aur amount confirm karein."
            if is_hi
            else "I need a little more detail. Please upload a clearer screenshot or confirm the 12-digit UTR and amount."
        )
    else:
        explanation_user = (
            "Aapki shikayat par jaanch chal rahi hai. Jald hi update diya jayega."
            if is_hi
            else "Your dispute inquiry is under review. An update will be provided shortly."
        )

    # --- Internal Operational / Compliance Explanation ---
    cbs_status = "DEBITED" if reconciliation.get("cbs_debited") else "NOT_DEBITED"
    npci_status = reconciliation.get("npcI_status") or "UNKNOWN"
    ben_status = "CREDITED" if reconciliation.get("beneficiary_credited") else "UNCONFIRMED"
    sett_status = reconciliation.get("paytm_settlement_status") or "PENDING"
    rule_matched = decision.get("rule_matched", "UNKNOWN_RULE")
    reasons_str = "; ".join(decision.get("reasons", []))

    explanation_internal = (
        f"DECISION={decision_str} | RULE={rule_matched} | "
        f"RISK_LEVEL={risk.get('risk_level')} (FraudScore={risk.get('fraud_score', 0):.1f}, RiskScore={risk.get('risk_score', 0):.1f}) | "
        f"FACTS: CBS={cbs_status}, NPCI={npci_status}, Beneficiary={ben_status}, PaytmSettlement={sett_status}, "
        f"DuplicateDebit={reconciliation.get('duplicate_debit')}, GhostSuccess={reconciliation.get('ghost_success')}, "
        f"InvalidUTR={reconciliation.get('invalid_utr')}. "
        f"REASONS: {reasons_str}"
    )

    return {
        "explanation_user": explanation_user,
        "explanation_internal": explanation_internal,
    }
