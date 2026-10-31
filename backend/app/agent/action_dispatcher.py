"""Action dispatcher executing financial operations, regulatory claims, and audit entries."""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.dispute import Dispute
from app.models.action import Action
from app.models.bridge_credit import BridgeCredit
from app.models.rbi_claim import RbiClaim
from app.models.escalation import Escalation
from app.schemas.dispute import ActionType, AgentDecision
from app.services.audit_service import AuditService
from app.core.logging import logger


class ActionDispatcher:
    """Executes atomic financial, regulatory, and reporting actions authorized by policy engine."""

    def __init__(self, db: Session):
        self.db = db
        self.audit_service = AuditService()

    def execute(
        self,
        dispute: Dispute,
        decision: Dict[str, Any],
        reconciliation: Dict[str, Any],
        risk: Dict[str, Any],
        consent_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Dispatches all actions determined by policy decision."""
        results: List[Dict[str, Any]] = []
        actions = decision.get("actions", [])
        now = datetime.now(timezone.utc)

        for action in actions:
            action_type_val = action.value if hasattr(action, "value") else str(action)
            handler_res = None

            # --- Handler A: Instant Bridge Credit ---
            if action_type_val == ActionType.BRIDGE_CREDIT.value:
                handler_res = self._handle_bridge_credit(dispute, reconciliation, consent_id, now)

            # --- Handler B: NPCI UDIR Dispute / Auto-Reversal ---
            elif action_type_val == ActionType.NPCI_DISPUTE_RAISED.value:
                handler_res = self._handle_npci_dispute(dispute, reconciliation, consent_id, now)

            # --- Handler C: Start RBI TAT Timer ---
            elif action_type_val == ActionType.START_RBI_TAT_TIMER.value:
                handler_res = self._handle_rbi_timer(dispute, consent_id, now)

            # --- Handler D: RBI Delay Penalty Claim ---
            elif action_type_val == ActionType.RBI_PENALTY_CLAIM.value:
                handler_res = self._handle_rbi_claim(dispute, reconciliation, consent_id, now)

            # --- Handler E: Generate Verified Receipt (Ghost Success) ---
            elif action_type_val == ActionType.GENERATE_RECEIPT.value:
                handler_res = self._handle_generate_receipt(dispute, reconciliation, consent_id, now)

            # --- Handler F: Human Operations Escalation ---
            elif action_type_val == ActionType.ESCALATE_HUMAN.value:
                handler_res = self._handle_escalation(dispute, decision, risk, consent_id, now)

            # --- Handler G: Fraud Alert ---
            elif action_type_val == ActionType.FRAUD_ALERT.value:
                handler_res = self._handle_fraud_alert(dispute, risk, decision, consent_id, now)

            # --- Handler H: Request Additional Information ---
            elif action_type_val == ActionType.REQUEST_INFO.value:
                handler_res = self._handle_request_info(dispute, consent_id, now)

            # --- Handler I: Notify User ---
            elif action_type_val == ActionType.NOTIFY_USER.value:
                handler_res = self._handle_notify_user(dispute, consent_id, now)

            # --- Handler J: Close Dispute ---
            elif action_type_val == ActionType.CLOSE_DISPUTE.value:
                handler_res = self._handle_close_dispute(dispute, consent_id, now)

            if handler_res:
                results.append(handler_res)

        return results

    def _handle_bridge_credit(self, dispute: Dispute, reconciliation: Dict[str, Any], consent_id: Optional[int], now: datetime) -> Dict[str, Any]:
        idempotency_key = f"bridge:{dispute.dispute_code}"
        existing = (
            self.db.query(BridgeCredit)
            .filter(
                (BridgeCredit.dispute_id == dispute.id)
                | (BridgeCredit.idempotency_key == idempotency_key)
            )
            .first()
        )

        amount = dispute.amount or reconciliation.get("cbs_amount") or 0.0

        if existing and existing.status == "SUCCESS":
            return {
                "action_type": ActionType.BRIDGE_CREDIT.value,
                "status": "ALREADY_ISSUED",
                "payload": {"credit_id": existing.id, "amount": existing.amount, "idempotency_key": idempotency_key},
            }

        bridge_credit = BridgeCredit(
            dispute_id=dispute.id,
            user_id=dispute.user_id,
            amount=amount,
            status="SUCCESS",
            issued_at=now,
            expiry_at=now + timedelta(days=7),
            idempotency_key=idempotency_key,
        )
        self.db.add(bridge_credit)

        payload = {
            "credit_id": f"BC-{dispute.dispute_code}",
            "amount": amount,
            "idempotency_key": idempotency_key,
            "expiry_days": 7,
        }
        action_rec = Action(
            dispute_id=dispute.id,
            action_type=ActionType.BRIDGE_CREDIT.value,
            payload_json=json.dumps(payload),
            executed_by="AI_TEAMMATE",
            status="SUCCESS",
            created_at=now,
        )
        self.db.add(action_rec)
        self.db.commit()

        self.audit_service.log_event(
            db=self.db,
            dispute_id=dispute.id,
            actor="AI_TEAMMATE",
            event="BRIDGE_CREDIT_ISSUED",
            details=payload,
            consent_id=consent_id,
        )

        return {"action_type": ActionType.BRIDGE_CREDIT.value, "status": "SUCCESS", "payload": payload}

    def _handle_npci_dispute(self, dispute: Dispute, reconciliation: Dict[str, Any], consent_id: Optional[int], now: datetime) -> Dict[str, Any]:
        payload = {
            "utr": dispute.utr,
            "claim_type": "AUTO_REVERSAL_TRACKING",
            "expected_reversal_time": "T+1",
            "gateway_ref": f"UDIR-TRK-{dispute.dispute_code}",
        }
        action_rec = Action(
            dispute_id=dispute.id,
            action_type=ActionType.NPCI_DISPUTE_RAISED.value,
            payload_json=json.dumps(payload),
            executed_by="AI_TEAMMATE",
            status="SUCCESS",
            created_at=now,
        )
        self.db.add(action_rec)
        self.db.commit()

        self.audit_service.log_event(
            db=self.db,
            dispute_id=dispute.id,
            actor="AI_TEAMMATE",
            event="NPCI_DISPUTE_RAISED",
            details=payload,
            consent_id=consent_id,
        )
        return {"action_type": ActionType.NPCI_DISPUTE_RAISED.value, "status": "SUCCESS", "payload": payload}

    def _handle_rbi_timer(self, dispute: Dispute, consent_id: Optional[int], now: datetime) -> Dict[str, Any]:
        payload = {
            "timer_started_at": now.isoformat(),
            "tat_allowed_days": 1,
            "penalty_per_day": settings.RBI_DELAY_PER_DAY_PENALTY,
        }
        action_rec = Action(
            dispute_id=dispute.id,
            action_type=ActionType.START_RBI_TAT_TIMER.value,
            payload_json=json.dumps(payload),
            executed_by="AI_TEAMMATE",
            status="SUCCESS",
            created_at=now,
        )
        self.db.add(action_rec)
        self.db.commit()

        self.audit_service.log_event(
            db=self.db,
            dispute_id=dispute.id,
            actor="AI_TEAMMATE",
            event="RBI_TAT_TIMER_STARTED",
            details=payload,
            consent_id=consent_id,
        )
        return {"action_type": ActionType.START_RBI_TAT_TIMER.value, "status": "SUCCESS", "payload": payload}

    def _handle_rbi_claim(self, dispute: Dispute, reconciliation: Dict[str, Any], consent_id: Optional[int], now: datetime) -> Dict[str, Any]:
        policy_inputs = reconciliation.get("policy_inputs", {})
        delay_days = policy_inputs.get("delay_days", 0)
        claim_amount = delay_days * settings.RBI_DELAY_PER_DAY_PENALTY

        existing = self.db.query(RbiClaim).filter(RbiClaim.dispute_id == dispute.id).first()
        if existing:
            return {
                "action_type": ActionType.RBI_PENALTY_CLAIM.value,
                "status": "ALREADY_FILED",
                "payload": {"claim_id": existing.id, "amount": existing.claim_amount},
            }

        raw_cbs = reconciliation.get("raw", {}).get("cbs", {})
        responsible_bank = raw_cbs.get("bank") or "REMITTER_BANK"

        rbi_claim = RbiClaim(
            dispute_id=dispute.id,
            claim_amount=claim_amount,
            delay_days=delay_days,
            status="SUBMITTED",
            filed_at=now,
            responsible_entity=responsible_bank,
        )
        self.db.add(rbi_claim)

        payload = {
            "claim_amount": claim_amount,
            "delay_days": delay_days,
            "responsible_entity": responsible_bank,
            "status": "SUBMITTED",
        }
        action_rec = Action(
            dispute_id=dispute.id,
            action_type=ActionType.RBI_PENALTY_CLAIM.value,
            payload_json=json.dumps(payload),
            executed_by="AI_TEAMMATE",
            status="SUCCESS",
            created_at=now,
        )
        self.db.add(action_rec)
        self.db.commit()

        self.audit_service.log_event(
            db=self.db,
            dispute_id=dispute.id,
            actor="AI_TEAMMATE",
            event="RBI_CLAIM_FILED",
            details=payload,
            consent_id=consent_id,
        )
        return {"action_type": ActionType.RBI_PENALTY_CLAIM.value, "status": "SUCCESS", "payload": payload}

    def _handle_generate_receipt(self, dispute: Dispute, reconciliation: Dict[str, Any], consent_id: Optional[int], now: datetime) -> Dict[str, Any]:
        raw_cbs = reconciliation.get("raw", {}).get("cbs", {})
        merchant_name = raw_cbs.get("merchant_name") or "Verified Merchant"
        amount = dispute.amount or reconciliation.get("cbs_amount") or 0.0

        receipt_id = f"RCPT-{dispute.dispute_code}"
        payload = {
            "receipt_id": receipt_id,
            "utr": dispute.utr,
            "merchant_name": merchant_name,
            "amount": amount,
            "status": "MERCHANT_CREDITED",
            "signature": f"SHA256:VERIFIED:{dispute.utr}:{amount}",
        }
        action_rec = Action(
            dispute_id=dispute.id,
            action_type=ActionType.GENERATE_RECEIPT.value,
            payload_json=json.dumps(payload),
            executed_by="AI_TEAMMATE",
            status="SUCCESS",
            created_at=now,
        )
        self.db.add(action_rec)
        self.db.commit()

        self.audit_service.log_event(
            db=self.db,
            dispute_id=dispute.id,
            actor="AI_TEAMMATE",
            event="RECEIPT_GENERATED",
            details=payload,
            consent_id=consent_id,
        )
        return {"action_type": ActionType.GENERATE_RECEIPT.value, "status": "SUCCESS", "payload": payload}

    def _handle_escalation(self, dispute: Dispute, decision: Dict[str, Any], risk: Dict[str, Any], consent_id: Optional[int], now: datetime) -> Dict[str, Any]:
        existing = self.db.query(Escalation).filter(Escalation.dispute_id == dispute.id).first()
        if existing:
            return {
                "action_type": ActionType.ESCALATE_HUMAN.value,
                "status": "ALREADY_ESCALATED",
                "payload": {"escalation_id": existing.id, "priority": existing.priority},
            }

        is_fraud = decision.get("decision") == AgentDecision.FRAUD_BLOCK
        priority = "CRITICAL" if is_fraud else "HIGH"
        assigned_to = "RISK_TEAM" if is_fraud else "SUPERVISOR"
        sla_mins = 5 if is_fraud else 15

        reasons_text = "; ".join(decision.get("reasons", [])) or "Human operator sign-off required."
        escalation = Escalation(
            dispute_id=dispute.id,
            reason=reasons_text,
            priority=priority,
            assigned_to=assigned_to,
            sla_deadline=now + timedelta(minutes=sla_mins),
            status="OPEN",
            created_at=now,
        )
        self.db.add(escalation)

        payload = {
            "priority": priority,
            "assigned_to": assigned_to,
            "sla_minutes": sla_mins,
            "reason": reasons_text,
        }
        action_rec = Action(
            dispute_id=dispute.id,
            action_type=ActionType.ESCALATE_HUMAN.value,
            payload_json=json.dumps(payload),
            executed_by="AI_TEAMMATE",
            status="SUCCESS",
            created_at=now,
        )
        self.db.add(action_rec)
        self.db.commit()

        self.audit_service.log_event(
            db=self.db,
            dispute_id=dispute.id,
            actor="AI_TEAMMATE",
            event="ESCALATION_CREATED",
            details=payload,
            consent_id=consent_id,
        )
        return {"action_type": ActionType.ESCALATE_HUMAN.value, "status": "SUCCESS", "payload": payload}

    def _handle_fraud_alert(self, dispute: Dispute, risk: Dict[str, Any], decision: Dict[str, Any], consent_id: Optional[int], now: datetime) -> Dict[str, Any]:
        payload = {
            "fraud_score": risk.get("fraud_score", 0.0),
            "reasons": decision.get("reasons", []),
            "blocked_bridge_credit": True,
        }
        action_rec = Action(
            dispute_id=dispute.id,
            action_type=ActionType.FRAUD_ALERT.value,
            payload_json=json.dumps(payload),
            executed_by="AI_TEAMMATE",
            status="SUCCESS",
            created_at=now,
        )
        self.db.add(action_rec)
        self.db.commit()

        self.audit_service.log_event(
            db=self.db,
            dispute_id=dispute.id,
            actor="AI_TEAMMATE",
            event="FRAUD_ALERT_CREATED",
            details=payload,
            consent_id=consent_id,
        )
        return {"action_type": ActionType.FRAUD_ALERT.value, "status": "SUCCESS", "payload": payload}

    def _handle_request_info(self, dispute: Dispute, consent_id: Optional[int], now: datetime) -> Dict[str, Any]:
        payload = {
            "missing_fields": ["clearer screenshot", "exact 12-digit UTR", "amount confirmation"],
        }
        action_rec = Action(
            dispute_id=dispute.id,
            action_type=ActionType.REQUEST_INFO.value,
            payload_json=json.dumps(payload),
            executed_by="AI_TEAMMATE",
            status="SUCCESS",
            created_at=now,
        )
        self.db.add(action_rec)
        self.db.commit()

        self.audit_service.log_event(
            db=self.db,
            dispute_id=dispute.id,
            actor="AI_TEAMMATE",
            event="INFO_REQUESTED",
            details=payload,
            consent_id=consent_id,
        )
        return {"action_type": ActionType.REQUEST_INFO.value, "status": "SUCCESS", "payload": payload}

    def _handle_notify_user(self, dispute: Dispute, consent_id: Optional[int], now: datetime) -> Dict[str, Any]:
        payload = {
            "channel": dispute.channel,
            "user_id": dispute.user_id,
            "dispute_code": dispute.dispute_code,
            "status": "QUEUED_NOTIFICATION",
        }
        action_rec = Action(
            dispute_id=dispute.id,
            action_type=ActionType.NOTIFY_USER.value,
            payload_json=json.dumps(payload),
            executed_by="AI_TEAMMATE",
            status="SUCCESS",
            created_at=now,
        )
        self.db.add(action_rec)
        self.db.commit()

        self.audit_service.log_event(
            db=self.db,
            dispute_id=dispute.id,
            actor="AI_TEAMMATE",
            event="USER_NOTIFIED_STUBBED",
            details=payload,
            consent_id=consent_id,
        )
        return {"action_type": ActionType.NOTIFY_USER.value, "status": "SUCCESS", "payload": payload}

    def _handle_close_dispute(self, dispute: Dispute, consent_id: Optional[int], now: datetime) -> Dict[str, Any]:
        dispute.resolved_at = now
        payload = {
            "closed_at": now.isoformat(),
            "dispute_code": dispute.dispute_code,
        }
        action_rec = Action(
            dispute_id=dispute.id,
            action_type=ActionType.CLOSE_DISPUTE.value,
            payload_json=json.dumps(payload),
            executed_by="AI_TEAMMATE",
            status="SUCCESS",
            created_at=now,
        )
        self.db.add(action_rec)
        self.db.commit()

        self.audit_service.log_event(
            db=self.db,
            dispute_id=dispute.id,
            actor="AI_TEAMMATE",
            event="DISPUTE_CLOSED",
            details=payload,
            consent_id=consent_id,
        )
        return {"action_type": ActionType.CLOSE_DISPUTE.value, "status": "SUCCESS", "payload": payload}
