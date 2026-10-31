"""Fintech regulatory policy decision engine adhering to RBI circulars and safety ceilings."""

from typing import Dict, Any, List
from app.schemas.dispute import AgentDecision, ActionType, RiskLevel
from app.core.config import settings


class PolicyEngine:
    """Applies deterministic governance rules to evaluate dispute facts and authorize remediation."""

    def __init__(
        self,
        auto_credit_ceiling: float = settings.AUTO_CREDIT_CEILING,
        min_trust_score: int = settings.MIN_TRUST_SCORE,
    ):
        self.auto_credit_ceiling = auto_credit_ceiling
        self.min_trust_score = min_trust_score

    def decide(
        self,
        reconciliation: Dict[str, Any],
        risk: Dict[str, Any],
        dispute: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Maps facts and risk signals to an actionable financial decision."""
        amount = dispute.get("amount") or reconciliation.get("cbs_amount") or 0.0
        policy_inputs = reconciliation.get("policy_inputs", {})
        risk_signals = reconciliation.get("risk_signals", {})
        trust_score = risk_signals.get("trust_score", 100)
        risk_level = risk.get("risk_level", "UNKNOWN")
        fraud_score = risk.get("fraud_score", 0.0)

        cbs_debited = reconciliation.get("cbs_debited", False)
        beneficiary_credited = reconciliation.get("beneficiary_credited", False)
        invalid_utr = reconciliation.get("invalid_utr", False)
        user_mismatch = reconciliation.get("user_mismatch", False)
        duplicate_debit = reconciliation.get("duplicate_debit", False)
        ghost_success = reconciliation.get("ghost_success", False)
        amount_mismatch = reconciliation.get("amount_mismatch", False)

        reasons = list(risk.get("reasons", []))

        # --- Rule 1: Fraud Control Block (Critical Risk) ---
        is_fraud = (
            invalid_utr
            or user_mismatch
            or risk_level == "CRITICAL"
            or fraud_score >= 50.0
            or policy_inputs.get("fraud_block_signal", False)
        )
        if is_fraud:
            return {
                "decision": AgentDecision.FRAUD_BLOCK,
                "actions": [ActionType.FRAUD_ALERT, ActionType.ESCALATE_HUMAN, ActionType.NOTIFY_USER],
                "rule_matched": "FRAUD_CONTROL_BLOCK",
                "eligible_for_bridge_credit": False,
                "requires_human_review": True,
                "fraud_block": True,
                "info_request": False,
                "reasons": reasons or ["Critical risk or fraudulent signal detected across switch"],
            }

        # --- Rule 2: Ghost Success (Merchant Credited -> Receipt Only) ---
        if ghost_success:
            return {
                "decision": AgentDecision.AUTO_RESOLVE,
                "actions": [ActionType.GENERATE_RECEIPT, ActionType.NOTIFY_USER, ActionType.CLOSE_DISPUTE],
                "rule_matched": "GHOST_SUCCESS_VERIFIED_RECEIPT",
                "eligible_for_bridge_credit": False,
                "requires_human_review": False,
                "fraud_block": False,
                "info_request": False,
                "reasons": ["Merchant ledger and NPCI confirm funds received. Generating digital receipt."],
            }

        # --- Rule 3: Missing / Ambiguous Information ---
        if policy_inputs.get("info_request_signal", False):
            return {
                "decision": AgentDecision.INFO_REQUEST,
                "actions": [ActionType.REQUEST_INFO, ActionType.NOTIFY_USER],
                "rule_matched": "MISSING_OR_AMBIGUOUS_EVIDENCE",
                "eligible_for_bridge_credit": False,
                "requires_human_review": False,
                "fraud_block": False,
                "info_request": True,
                "reasons": ["Missing or ambiguous evidence requires clarification from user."],
            }

        # --- Rule 4: High Value / Human-in-the-Loop Review ---
        requires_review = (
            policy_inputs.get("requires_human_review_signal", False)
            or amount > self.auto_credit_ceiling
            or risk_level in ["HIGH", "CRITICAL"]
            or duplicate_debit
            or amount_mismatch
            or (60 <= trust_score < self.min_trust_score)
        )
        if requires_review:
            if amount > self.auto_credit_ceiling:
                reasons.append(f"Amount INR {amount} exceeds autonomous ceiling INR {self.auto_credit_ceiling}")
            if duplicate_debit:
                reasons.append("Duplicate debit pattern requires supervisor review")

            return {
                "decision": AgentDecision.HUMAN_ESCALATE,
                "actions": [ActionType.ESCALATE_HUMAN, ActionType.NOTIFY_USER],
                "rule_matched": "HUMAN_IN_LOOP_ESCALATION",
                "eligible_for_bridge_credit": False,
                "requires_human_review": True,
                "fraud_block": False,
                "info_request": False,
                "reasons": reasons or ["Transaction characteristics require human supervisor sign-off"],
            }

        # --- Rule 5: Auto-Resolve with Instant Bridge Credit ---
        can_auto_resolve = (
            cbs_debited
            and not beneficiary_credited
            and not invalid_utr
            and not user_mismatch
            and not duplicate_debit
            and not ghost_success
            and amount <= self.auto_credit_ceiling
            and trust_score >= self.min_trust_score
            and fraud_score < 50.0
            and (risk_level == "LOW" or policy_inputs.get("eligible_for_automatic_bridge_credit_signal", False))
        )
        if can_auto_resolve:
            actions = [
                ActionType.BRIDGE_CREDIT,
                ActionType.NPCI_DISPUTE_RAISED,
                ActionType.START_RBI_TAT_TIMER,
                ActionType.NOTIFY_USER,
            ]
            if policy_inputs.get("rbi_compensation_signal", False):
                actions.append(ActionType.RBI_PENALTY_CLAIM)

            return {
                "decision": AgentDecision.AUTO_RESOLVE,
                "actions": actions,
                "rule_matched": "RBI_TAT_BRIDGE_CREDIT_LOW_RISK",
                "eligible_for_bridge_credit": True,
                "requires_human_review": False,
                "fraud_block": False,
                "info_request": False,
                "reasons": [
                    "CBS debit confirmed",
                    "NPCI indicates beneficiary timeout",
                    "Merchant not credited",
                    "Amount within safe autonomous ceiling",
                    "User trust score is high",
                ],
            }

        # --- Rule 6: Fallback Safe Escalation ---
        return {
            "decision": AgentDecision.HUMAN_ESCALATE,
            "actions": [ActionType.ESCALATE_HUMAN, ActionType.NOTIFY_USER],
            "rule_matched": "DEFAULT_SAFE_ESCALATION",
            "eligible_for_bridge_credit": False,
            "requires_human_review": True,
            "fraud_block": False,
            "info_request": False,
            "reasons": reasons or ["Fallback safety policy routed dispute to operations queue"],
        }
