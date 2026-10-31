"""Autonomous agent state machine and orchestrator for self-healing UPI disputes."""

import json
from enum import Enum
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.dispute import Dispute
from app.models.transaction import Transaction
from app.schemas.dispute import AgentDecision, DisputeStatus, RiskLevel, ActionType
from app.services.reconciliation_service import ReconciliationService
from app.services.consent_service import ConsentService
from app.services.audit_service import AuditService
from app.agent.risk_engine import RiskEngine
from app.agent.policy_engine import PolicyEngine
from app.agent.action_dispatcher import ActionDispatcher
from app.agent.explanations import generate_explanations
from app.core.logging import logger


class AgentState(str, Enum):
    IDLE = "IDLE"
    INGESTING_EVIDENCE = "INGESTING_EVIDENCE"
    VERIFYING_IDENTITY = "VERIFYING_IDENTITY"
    TAKING_CONSENT = "TAKING_CONSENT"
    CHECKING_LEDGERS = "CHECKING_LEDGERS"
    ASSESSING_RISK = "ASSESSING_RISK"
    APPLYING_POLICY = "APPLYING_POLICY"
    DISPATCHING_ACTIONS = "DISPATCHING_ACTIONS"
    EXPLAINING_DECISION = "EXPLAINING_DECISION"
    COMPLETED = "COMPLETED"
    ESCALATED = "ESCALATED"
    FRAUD_BLOCKED = "FRAUD_BLOCKED"
    INFO_REQUESTED = "INFO_REQUESTED"
    FAILED = "FAILED"


class AgentStateMachine:
    """Tracks state lifecycle transitions and logs structured traces."""

    def __init__(self, dispute_id: int):
        self.dispute_id = dispute_id
        self.current_state: AgentState = AgentState.IDLE
        self.history: List[Dict[str, Any]] = []

    def transition_to(self, new_state: AgentState, reason: str = "") -> None:
        """Transitions orchestrator state and appends timestamped trace."""
        logger.info(
            f"Dispute {self.dispute_id}: {self.current_state.value} -> {new_state.value} ({reason})"
        )
        self.history.append({
            "from_state": self.current_state.value,
            "to_state": new_state.value,
            "reason": reason,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        self.current_state = new_state

    def get_state(self) -> AgentState:
        return self.current_state


class AgentOrchestrator:
    """Executes the full end-to-end autonomous resolution workflow for a dispute."""

    def __init__(self, db: Session):
        self.db = db
        self.reconciliation_service = ReconciliationService(db=db)
        self.risk_engine = RiskEngine()
        self.policy_engine = PolicyEngine()
        self.action_dispatcher = ActionDispatcher(db=db)
        self.audit_service = AuditService()

    def run_for_dispute(self, dispute_id: int) -> Dict[str, Any]:
        """Runs the complete 10-step autonomous resolution lifecycle for a dispute."""
        dispute = self.db.query(Dispute).filter(Dispute.id == dispute_id).first()
        if not dispute:
            raise ValueError(f"Dispute with ID {dispute_id} does not exist.")

        sm = AgentStateMachine(dispute_id=dispute.id)

        # Step 1: Ingesting Evidence
        sm.transition_to(AgentState.INGESTING_EVIDENCE, "Loaded dispute record and evidence")
        self.audit_service.log_event(
            db=self.db,
            dispute_id=dispute.id,
            actor="AI_TEAMMATE",
            event="AGENT_RUN_STARTED",
            details={"dispute_code": dispute.dispute_code, "utr": dispute.utr},
        )

        # Step 2: Verifying Identity
        sm.transition_to(AgentState.VERIFYING_IDENTITY, "Verifying transaction ownership against user account")
        txn = self.db.query(Transaction).filter(Transaction.utr == dispute.utr).first() if dispute.utr else None
        if txn:
            dispute.transaction_id = txn.id
            dispute.identity_verified = (txn.user_id == dispute.user_id)
            if not dispute.amount:
                dispute.amount = txn.amount
        else:
            dispute.identity_verified = False

        self.audit_service.log_event(
            db=self.db,
            dispute_id=dispute.id,
            actor="AI_TEAMMATE",
            event="IDENTITY_VERIFIED" if dispute.identity_verified else "IDENTITY_MISMATCH",
            details={"identity_verified": dispute.identity_verified, "dispute_user_id": dispute.user_id},
        )

        # Step 3: Taking Consent
        sm.transition_to(AgentState.TAKING_CONSENT, "Checking active user authorization scopes")
        consent_info = ConsentService.ensure_consent_sync(
            db=self.db,
            user_id=dispute.user_id,
            channel=dispute.channel or "SIMULATOR",
        )
        dispute.consent_id = consent_info.get("consent_id")
        self.audit_service.log_event(
            db=self.db,
            dispute_id=dispute.id,
            actor="AI_TEAMMATE",
            event="CONSENT_REUSED" if consent_info.get("reused") else "CONSENT_CREATED",
            details=consent_info,
            consent_id=dispute.consent_id,
        )

        # Step 4: Checking Ledgers (Three-Way Reconciliation)
        sm.transition_to(AgentState.CHECKING_LEDGERS, "Executing 3-way check across CBS, NPCI, and Paytm")
        claimed_amt = dispute.claimed_amount or dispute.amount
        reconciliation = self.reconciliation_service.reconcile(
            utr=dispute.utr or "",
            user_id=dispute.user_id,
            claimed_amount=claimed_amt,
            channel=dispute.channel or "SIMULATOR",
        )
        dispute.three_way_json = json.dumps(reconciliation)
        if not dispute.amount and reconciliation.get("cbs_amount"):
            dispute.amount = reconciliation["cbs_amount"]

        self.audit_service.log_event(
            db=self.db,
            dispute_id=dispute.id,
            actor="AI_TEAMMATE",
            event="RECONCILIATION_COMPLETED",
            details={
                "cbs_debited": reconciliation.get("cbs_debited"),
                "beneficiary_credited": reconciliation.get("beneficiary_credited"),
                "invalid_utr": reconciliation.get("invalid_utr"),
            },
            consent_id=dispute.consent_id,
        )

        # Step 5: Assessing Risk
        sm.transition_to(AgentState.ASSESSING_RISK, "Calculating deterministic fraud score and operational risk")
        risk = self.risk_engine.evaluate(reconciliation=reconciliation)
        dispute.risk_score = risk["risk_score"]
        dispute.fraud_score = risk["fraud_score"]
        dispute.risk_level = risk["risk_level"]

        self.audit_service.log_event(
            db=self.db,
            dispute_id=dispute.id,
            actor="AI_TEAMMATE",
            event="RISK_EVALUATED",
            details=risk,
            consent_id=dispute.consent_id,
        )

        # Step 6: Applying Policy
        sm.transition_to(AgentState.APPLYING_POLICY, "Applying RBI guidelines and autonomous limits")
        dispute_info = {
            "dispute_id": dispute.id,
            "dispute_code": dispute.dispute_code,
            "user_id": dispute.user_id,
            "amount": dispute.amount,
            "channel": dispute.channel,
        }
        policy_decision = self.policy_engine.decide(
            reconciliation=reconciliation,
            risk=risk,
            dispute=dispute_info,
        )
        dec_val = policy_decision["decision"]
        dispute.agent_decision = dec_val.value if hasattr(dec_val, "value") else str(dec_val)
        actions_list = [a.value if hasattr(a, "value") else str(a) for a in policy_decision["actions"]]
        dispute.recommended_actions_json = json.dumps(actions_list)

        self.audit_service.log_event(
            db=self.db,
            dispute_id=dispute.id,
            actor="AI_TEAMMATE",
            event="POLICY_DECIDED",
            details={"decision": dispute.agent_decision, "actions": actions_list},
            consent_id=dispute.consent_id,
        )

        # Step 7: Dispatching Actions
        sm.transition_to(AgentState.DISPATCHING_ACTIONS, f"Dispatching {len(actions_list)} authorized actions")
        action_results = self.action_dispatcher.execute(
            dispute=dispute,
            decision=policy_decision,
            reconciliation=reconciliation,
            risk=risk,
            consent_id=dispute.consent_id,
        )
        dispute.action_summary_json = json.dumps(action_results)

        # Update dispute status according to decision and actions
        if dispute.agent_decision == AgentDecision.AUTO_RESOLVE.value:
            if reconciliation.get("ghost_success"):
                dispute.status = DisputeStatus.RECEIPT_GENERATED.value
            else:
                dispute.status = DisputeStatus.AUTO_CREDITED.value
            dispute.resolved_at = datetime.now(timezone.utc)
        elif dispute.agent_decision == AgentDecision.FRAUD_BLOCK.value:
            dispute.status = DisputeStatus.FRAUD_BLOCKED.value
        elif dispute.agent_decision == AgentDecision.INFO_REQUEST.value:
            dispute.status = DisputeStatus.INFO_REQUESTED.value
        else:
            dispute.status = DisputeStatus.ESCALATED.value

        self.audit_service.log_event(
            db=self.db,
            dispute_id=dispute.id,
            actor="AI_TEAMMATE",
            event="ACTIONS_DISPATCHED",
            details={"actions_executed_count": len(action_results), "status": dispute.status},
            consent_id=dispute.consent_id,
        )

        # Step 8: Explaining Decision
        sm.transition_to(AgentState.EXPLAINING_DECISION, "Synthesizing bilingual explanations")
        explanations = generate_explanations(
            decision=policy_decision,
            reconciliation=reconciliation,
            risk=risk,
            dispute=dispute_info,
            user_language=dispute.language or "hi",
        )
        dispute.explanation_user = explanations["explanation_user"]
        dispute.explanation_internal = explanations["explanation_internal"]

        self.audit_service.log_event(
            db=self.db,
            dispute_id=dispute.id,
            actor="AI_TEAMMATE",
            event="EXPLANATION_GENERATED",
            details={"language": dispute.language or "hi"},
            consent_id=dispute.consent_id,
        )

        # Step 9: Final State Transition
        if dispute.agent_decision == AgentDecision.AUTO_RESOLVE.value:
            sm.transition_to(AgentState.COMPLETED, "Dispute successfully self-healed")
        elif dispute.agent_decision == AgentDecision.FRAUD_BLOCK.value:
            sm.transition_to(AgentState.FRAUD_BLOCKED, "Dispute blocked due to high fraud score")
        elif dispute.agent_decision == AgentDecision.INFO_REQUEST.value:
            sm.transition_to(AgentState.INFO_REQUESTED, "Requested additional evidence from user")
        else:
            sm.transition_to(AgentState.ESCALATED, "Dispute routed to human operations team")

        dispute.state_history_json = json.dumps(sm.history)
        self.db.commit()
        self.db.refresh(dispute)

        self.audit_service.log_event(
            db=self.db,
            dispute_id=dispute.id,
            actor="AI_TEAMMATE",
            event="AGENT_RUN_COMPLETED",
            details={"final_state": sm.get_state().value, "status": dispute.status},
            consent_id=dispute.consent_id,
        )

        resolved_bool = dispute.status in [
            DisputeStatus.AUTO_CREDITED.value,
            DisputeStatus.RECEIPT_GENERATED.value,
            DisputeStatus.RESOLVED.value,
        ]

        formatted_actions = [
            {
                "action_type": a.get("action_type"),
                "status": a.get("status"),
                "payload": a.get("payload", {}),
            }
            for a in action_results
        ]

        return {
            "dispute_id": dispute.id,
            "dispute_code": dispute.dispute_code,
            "utr": dispute.utr or "",
            "user_id": dispute.user_id,
            "amount": dispute.amount,
            "decision": dispute.agent_decision,
            "risk_level": dispute.risk_level,
            "fraud_score": dispute.fraud_score,
            "risk_score": dispute.risk_score,
            "actions_executed": formatted_actions,
            "explanation_user": dispute.explanation_user or "",
            "explanation_internal": dispute.explanation_internal or "",
            "three_way": reconciliation,
            "risk": risk,
            "policy": policy_decision,
            "state_history": sm.history,
            "status": dispute.status,
            "resolved": resolved_bool,
        }
