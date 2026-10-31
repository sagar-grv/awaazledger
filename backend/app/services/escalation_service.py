"""Escalation service managing supervisor workflows and audited interventions."""

import os
import json
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import case, desc

from app.models.escalation import Escalation
from app.models.dispute import Dispute
from app.models.user import User
from app.models.transaction import Transaction
from app.models.action import Action
from app.models.audit_log import AuditLog
from app.models.bridge_credit import BridgeCredit
from app.models.evidence import Evidence
from app.schemas.escalation import (
    EscalationResponse,
    EscalationListResponse,
    EscalationDetailResponse,
    SupervisorActionResponse,
)

_DEMO_PHONE_MAP = {
    1: "+919876543210",
    2: "+919876543211",
    3: "+919876543212",
    4: "+919876543213",
    5: "+919876543214",
}


class EscalationService:
    def __init__(self, db: Session):
        self.db = db

    def _get_user_phone(self, user: Optional[User]) -> Optional[str]:
        if not user:
            return None
        return _DEMO_PHONE_MAP.get(user.id) or getattr(user, "paytm_id", None)

    def _build_response_item(self, esc: Escalation, dispute: Optional[Dispute] = None, user: Optional[User] = None) -> EscalationResponse:
        now = datetime.now(timezone.utc)
        is_breached = False
        hours_to_sla = None

        if esc.sla_deadline:
            deadline = esc.sla_deadline
            if deadline.tzinfo is None:
                deadline = deadline.replace(tzinfo=timezone.utc)
            delta = (deadline - now).total_seconds() / 3600.0
            hours_to_sla = round(delta, 2)
            if delta < 0 and esc.status in ("OPEN", "IN_REVIEW"):
                is_breached = True

        return EscalationResponse(
            id=esc.id,
            dispute_id=esc.dispute_id,
            dispute_code=dispute.dispute_code if dispute else None,
            user_name=user.name if user else None,
            user_phone=self._get_user_phone(user),
            amount=dispute.claimed_amount or dispute.amount or 0.0 if dispute else 0.0,
            priority=esc.priority,
            reason=esc.reason,
            assigned_to=esc.assigned_to,
            sla_deadline=esc.sla_deadline,
            status=esc.status,
            resolution_note=esc.resolution_note,
            resolution_notes=esc.resolution_note,
            created_at=esc.created_at,
            resolved_at=esc.resolved_at,
            updated_at=getattr(esc, "updated_at", None),
            is_sla_breached=is_breached,
            hours_to_sla=hours_to_sla,
        )

    def list_escalations(
        self,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        assigned_to: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> EscalationListResponse:
        try:
            limit = int(limit.default if hasattr(limit, "default") else limit)
        except Exception:
            limit = 50
        try:
            offset = int(offset.default if hasattr(offset, "default") else offset)
        except Exception:
            offset = 0

        query = (
            self.db.query(Escalation, Dispute, User)
            .join(Dispute, Escalation.dispute_id == Dispute.id)
            .outerjoin(User, Dispute.user_id == User.id)
        )

        if status:
            query = query.filter(Escalation.status == status)
        if priority:
            query = query.filter(Escalation.priority == priority)
        if assigned_to:
            query = query.filter(Escalation.assigned_to == assigned_to)

        # Priority weight ordering: CRITICAL=1, HIGH=2, MEDIUM=3, LOW=4
        priority_order = case(
            (Escalation.priority == "CRITICAL", 1),
            (Escalation.priority == "HIGH", 2),
            (Escalation.priority == "MEDIUM", 3),
            else_=4,
        )

        results = query.order_by(priority_order, Escalation.created_at.desc()).offset(offset).limit(limit).all()

        items = [self._build_response_item(esc, dispute, user) for esc, dispute, user in results]

        total = query.count()
        open_count = self.db.query(Escalation).filter(Escalation.status.in_(["OPEN", "IN_REVIEW"])).count()

        now = datetime.now(timezone.utc)
        sla_breached_count = 0
        all_open = self.db.query(Escalation).filter(Escalation.status.in_(["OPEN", "IN_REVIEW"])).all()
        for e in all_open:
            if e.sla_deadline:
                dl = e.sla_deadline
                if dl.tzinfo is None:
                    dl = dl.replace(tzinfo=timezone.utc)
                if dl < now:
                    sla_breached_count += 1

        return EscalationListResponse(
            items=items,
            total=total,
            open_count=open_count,
            sla_breached_count=sla_breached_count,
        )

    def get_escalation_detail(self, escalation_id: int) -> EscalationDetailResponse:
        res = (
            self.db.query(Escalation, Dispute, User)
            .join(Dispute, Escalation.dispute_id == Dispute.id)
            .outerjoin(User, Dispute.user_id == User.id)
            .filter(Escalation.id == escalation_id)
            .first()
        )
        if not res:
            raise ValueError(f"Escalation ticket {escalation_id} not found")

        esc, dispute, user = res

        txn_dict = None
        if dispute.transaction_id:
            txn = self.db.query(Transaction).filter(Transaction.id == dispute.transaction_id).first()
            if txn:
                txn_dict = {
                    "id": txn.id,
                    "utr": txn.utr,
                    "amount": txn.amount,
                    "currency": txn.currency,
                    "bank": txn.bank,
                    "merchant_name": txn.merchant_name,
                    "merchant_vpa": txn.merchant_vpa,
                    "cbs_status": txn.cbs_status,
                    "npci_status": getattr(txn, "npcI_status", "UNKNOWN"),
                    "beneficiary_status": txn.beneficiary_status,
                    "settlement_status": txn.settlement_status,
                    "created_at": txn.created_at.isoformat() if txn.created_at else None,
                }

        # Deserialized payloads
        three_way = json.loads(dispute.three_way_json) if dispute.three_way_json else None
        rec_actions = json.loads(dispute.recommended_actions_json) if dispute.recommended_actions_json else []
        action_summary = json.loads(dispute.action_summary_json) if dispute.action_summary_json else None

        # Fetch actions
        actions = (
            self.db.query(Action)
            .filter(Action.dispute_id == dispute.id)
            .order_by(Action.created_at.asc())
            .all()
        )
        actions_list = [
            {
                "id": a.id,
                "action_type": a.action_type,
                "executed_by": a.executed_by,
                "status": a.status,
                "payload": json.loads(a.payload_json) if a.payload_json else None,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in actions
        ]

        # Fetch audit trail
        logs = (
            self.db.query(AuditLog)
            .filter(AuditLog.dispute_id == dispute.id)
            .order_by(AuditLog.timestamp.asc())
            .all()
        )
        audit_list = [
            {
                "id": l.id,
                "actor": l.actor,
                "event": l.event,
                "output_status": l.output_status,
                "details": json.loads(l.details_json) if l.details_json else None,
                "timestamp": l.timestamp.isoformat() if l.timestamp else None,
            }
            for l in logs
        ]

        # Fetch evidence
        evidences = (
            self.db.query(Evidence)
            .filter(Evidence.dispute_id == dispute.id)
            .order_by(Evidence.created_at.asc())
            .all()
        )
        evidence_list = [
            {
                "id": ev.id,
                "evidence_type": ev.evidence_type,
                "source": ev.source,
                "raw_text": ev.raw_text,
                "parsed_data": json.loads(ev.parsed_data_json) if ev.parsed_data_json else None,
                "created_at": ev.created_at.isoformat() if ev.created_at else None,
            }
            for ev in evidences
        ]

        risk_assessment = {
            "risk_score": dispute.risk_score,
            "fraud_score": dispute.fraud_score,
            "risk_level": dispute.risk_level,
            "confidence_score": dispute.confidence_score,
            "identity_verified": dispute.identity_verified,
        }

        policy_evaluation = {
            "agent_decision": dispute.agent_decision,
            "recommended_actions": rec_actions,
            "action_summary": action_summary,
            "explanation_internal": dispute.explanation_internal,
            "explanation_user": dispute.explanation_user,
        }

        user_dict = {
            "id": user.id if user else None,
            "phone": self._get_user_phone(user),
            "name": user.name if user else None,
            "paytm_id": user.paytm_id if user else None,
            "trust_score": user.trust_score if user else 100,
            "previous_dispute_count": user.previous_dispute_count if user else 0,
            "kyc_status": user.kyc_status if user else "UNKNOWN",
        }

        dispute_dict = {
            "id": dispute.id,
            "dispute_code": dispute.dispute_code,
            "utr": dispute.utr,
            "claimed_amount": dispute.claimed_amount or dispute.amount,
            "channel": dispute.channel,
            "intent": dispute.intent,
            "language": dispute.language,
            "transcript": dispute.transcript,
            "status": dispute.status,
            "agent_decision": dispute.agent_decision,
            "created_at": dispute.created_at.isoformat() if dispute.created_at else None,
            "resolved_at": dispute.resolved_at.isoformat() if dispute.resolved_at else None,
        }

        return EscalationDetailResponse(
            escalation=self._build_response_item(esc, dispute, user),
            dispute=dispute_dict,
            user=user_dict,
            transaction=txn_dict,
            three_way_reconciliation=three_way,
            risk_assessment=risk_assessment,
            policy_evaluation=policy_evaluation,
            actions_taken=actions_list,
            audit_trail=audit_list,
            evidence_items=evidence_list,
        )

    def approve_escalation(
        self,
        escalation_id: int,
        note: Optional[str] = None,
        supervisor_id: str = "SUPERVISOR_L2",
    ) -> SupervisorActionResponse:
        esc = self.db.query(Escalation).filter(Escalation.id == escalation_id).first()
        if not esc:
            raise ValueError(f"Escalation ticket {escalation_id} not found")

        dispute = self.db.query(Dispute).filter(Dispute.id == esc.dispute_id).first()
        if not dispute:
            raise ValueError(f"Dispute {esc.dispute_id} not found")

        now = datetime.now(timezone.utc)

        # Idempotency check: if already approved, return existing state
        if esc.status == "APPROVED":
            existing_bc = self.db.query(BridgeCredit).filter(BridgeCredit.dispute_id == dispute.id).first()
            return SupervisorActionResponse(
                escalation_id=esc.id,
                dispute_id=dispute.id,
                action="APPROVE",
                status="ALREADY_APPROVED",
                message=f"Escalation {escalation_id} was already approved.",
                bridge_credit_id=existing_bc.id if existing_bc else None,
                timestamp=now,
            )

        esc.status = "APPROVED"
        esc.resolution_note = note or "Manually approved by supervisor with bridge credit credit line."
        esc.resolved_at = now
        esc.updated_at = now

        dispute.status = "RESOLVED"
        dispute.agent_decision = "MANUALLY_APPROVED"
        dispute.resolved_at = now
        dispute.explanation_internal = (
            f"Supervisor {supervisor_id} manually approved dispute {dispute.dispute_code}. "
            f"Note: {esc.resolution_note}"
        )
        dispute.explanation_user = (
            f"AwaazLedger Supervisor has approved your claim for INR {dispute.claimed_amount or dispute.amount:.2f}. "
            f"Bridge credit has been deposited to your account."
        )

        # Issue Bridge Credit
        amount = dispute.claimed_amount or dispute.amount or 0.0
        idempotency_key = f"manual-bridge:{dispute.dispute_code}"
        bc = self.db.query(BridgeCredit).filter(BridgeCredit.idempotency_key == idempotency_key).first()
        if not bc:
            bc = BridgeCredit(
                dispute_id=dispute.id,
                user_id=dispute.user_id,
                amount=amount,
                status="ISSUED",
                issued_at=now,
                idempotency_key=idempotency_key,
            )
            self.db.add(bc)
            self.db.flush()

        # Audited Action
        act = Action(
            dispute_id=dispute.id,
            action_type="BRIDGE_CREDIT_ISSUED",
            payload_json=json.dumps({
                "amount": amount,
                "recipient_user_id": dispute.user_id,
                "approved_by": supervisor_id,
                "note": note,
            }),
            executed_by=supervisor_id,
            status="COMPLETED",
            created_at=now,
        )
        self.db.add(act)

        # Audit Log
        audit = AuditLog(
            dispute_id=dispute.id,
            actor=supervisor_id,
            event="ESCALATION_APPROVED",
            output_status="SUCCESS",
            details_json=json.dumps({
                "escalation_id": esc.id,
                "bridge_credit_id": bc.id,
                "amount": amount,
                "note": note,
            }),
            timestamp=now,
        )
        self.db.add(audit)

        self.db.commit()

        return SupervisorActionResponse(
            escalation_id=esc.id,
            dispute_id=dispute.id,
            action="APPROVE",
            status="APPROVED",
            message=f"Escalation approved successfully. Bridge credit of INR {amount:.2f} issued.",
            bridge_credit_id=bc.id,
            timestamp=now,
        )

    def reject_escalation(
        self,
        escalation_id: int,
        reason: Optional[str] = None,
        note: Optional[str] = None,
        supervisor_id: str = "SUPERVISOR_L2",
    ) -> SupervisorActionResponse:
        esc = self.db.query(Escalation).filter(Escalation.id == escalation_id).first()
        if not esc:
            raise ValueError(f"Escalation ticket {escalation_id} not found")

        dispute = self.db.query(Dispute).filter(Dispute.id == esc.dispute_id).first()
        if not dispute:
            raise ValueError(f"Dispute {esc.dispute_id} not found")

        now = datetime.now(timezone.utc)
        note_text = note or reason or "Manually rejected by supervisor after investigation."

        esc.status = "REJECTED"
        esc.resolution_note = note_text
        esc.resolved_at = now
        esc.updated_at = now

        dispute.status = "REJECTED"
        dispute.agent_decision = "MANUALLY_REJECTED"
        dispute.resolved_at = now
        dispute.explanation_internal = f"Supervisor {supervisor_id} rejected claim. Note: {note_text}"
        dispute.explanation_user = (
            f"After manual supervisor review, your dispute could not be approved. Reason: {note_text}"
        )

        # Audited Action
        act = Action(
            dispute_id=dispute.id,
            action_type="NOTIFY_USER",
            payload_json=json.dumps({
                "rejected_by": supervisor_id,
                "reason": note_text,
            }),
            executed_by=supervisor_id,
            status="COMPLETED",
            created_at=now,
        )
        self.db.add(act)

        # Audit Log
        audit = AuditLog(
            dispute_id=dispute.id,
            actor=supervisor_id,
            event="ESCALATION_REJECTED",
            output_status="REJECTED",
            details_json=json.dumps({
                "escalation_id": esc.id,
                "supervisor_id": supervisor_id,
                "reason": note_text,
            }),
            timestamp=now,
        )
        self.db.add(audit)

        self.db.commit()

        return SupervisorActionResponse(
            escalation_id=esc.id,
            dispute_id=dispute.id,
            action="REJECT",
            status="REJECTED",
            message=f"Escalation rejected: {note_text}",
            bridge_credit_id=None,
            timestamp=now,
        )

    def request_info(
        self,
        escalation_id: int,
        prompt: Optional[str] = None,
        note: Optional[str] = None,
        supervisor_id: str = "SUPERVISOR_L2",
    ) -> SupervisorActionResponse:
        esc = self.db.query(Escalation).filter(Escalation.id == escalation_id).first()
        if not esc:
            raise ValueError(f"Escalation ticket {escalation_id} not found")

        dispute = self.db.query(Dispute).filter(Dispute.id == esc.dispute_id).first()
        if not dispute:
            raise ValueError(f"Dispute {esc.dispute_id} not found")

        now = datetime.now(timezone.utc)
        prompt_text = prompt or note or "Please provide the bank account statement or merchant confirmation screenshot."

        esc.status = "INFO_REQUESTED"
        esc.resolution_note = f"Info requested: {prompt_text}"
        esc.updated_at = now

        dispute.status = "INFO_REQUESTED"
        dispute.agent_decision = "REQUEST_INFO"
        dispute.explanation_internal = f"Supervisor {supervisor_id} requested additional customer info: {prompt_text}"
        dispute.explanation_user = f"AwaazLedger needs more information to proceed: {prompt_text}"

        act = Action(
            dispute_id=dispute.id,
            action_type="REQUEST_INFO",
            payload_json=json.dumps({
                "requested_by": supervisor_id,
                "prompt": prompt_text,
            }),
            executed_by=supervisor_id,
            status="COMPLETED",
            created_at=now,
        )
        self.db.add(act)

        audit = AuditLog(
            dispute_id=dispute.id,
            actor=supervisor_id,
            event="ESCALATION_INFO_REQUESTED",
            output_status="PENDING_USER_INPUT",
            details_json=json.dumps({
                "escalation_id": esc.id,
                "prompt": prompt_text,
            }),
            timestamp=now,
        )
        self.db.add(audit)

        self.db.commit()

        return SupervisorActionResponse(
            escalation_id=esc.id,
            dispute_id=dispute.id,
            action="REQUEST_INFO",
            status="INFO_REQUESTED",
            message=f"Additional info requested from user: {prompt_text}",
            bridge_credit_id=None,
            timestamp=now,
        )

    def mark_fraud(
        self,
        escalation_id: int,
        reason: Optional[str] = None,
        note: Optional[str] = None,
        supervisor_id: str = "SUPERVISOR_L2",
    ) -> SupervisorActionResponse:
        esc = self.db.query(Escalation).filter(Escalation.id == escalation_id).first()
        if not esc:
            raise ValueError(f"Escalation ticket {escalation_id} not found")

        dispute = self.db.query(Dispute).filter(Dispute.id == esc.dispute_id).first()
        if not dispute:
            raise ValueError(f"Dispute {esc.dispute_id} not found")

        now = datetime.now(timezone.utc)
        fraud_reason = reason or note or "Fraudulent claim pattern confirmed by supervisor."

        esc.status = "FRAUD_CONFIRMED"
        esc.resolution_note = fraud_reason
        esc.resolved_at = now
        esc.updated_at = now

        dispute.status = "FRAUD_BLOCKED"
        dispute.agent_decision = "MANUALLY_BLOCKED_FRAUD"
        dispute.resolved_at = now
        dispute.explanation_internal = f"Supervisor {supervisor_id} marked as FRAUD. Details: {fraud_reason}"
        dispute.explanation_user = "This dispute cannot be processed due to verification and risk security policies."

        act = Action(
            dispute_id=dispute.id,
            action_type="FRAUD_ALERT",
            payload_json=json.dumps({
                "marked_by": supervisor_id,
                "reason": fraud_reason,
            }),
            executed_by=supervisor_id,
            status="COMPLETED",
            created_at=now,
        )
        self.db.add(act)

        audit = AuditLog(
            dispute_id=dispute.id,
            actor=supervisor_id,
            event="ESCALATION_FRAUD_MARKED",
            output_status="FRAUD_BLOCKED",
            details_json=json.dumps({
                "escalation_id": esc.id,
                "reason": fraud_reason,
            }),
            timestamp=now,
        )
        self.db.add(audit)

        self.db.commit()

        return SupervisorActionResponse(
            escalation_id=esc.id,
            dispute_id=dispute.id,
            action="MARK_FRAUD",
            status="FRAUD_CONFIRMED",
            message=f"Dispute marked as fraud and blocked: {fraud_reason}",
            bridge_credit_id=None,
            timestamp=now,
        )

    def assign_escalation(
        self,
        escalation_id: int,
        assigned_to: str,
        supervisor_id: str = "SUPERVISOR_L2",
        note: Optional[str] = None,
    ) -> SupervisorActionResponse:
        esc = self.db.query(Escalation).filter(Escalation.id == escalation_id).first()
        if not esc:
            raise ValueError(f"Escalation ticket {escalation_id} not found")

        dispute = self.db.query(Dispute).filter(Dispute.id == esc.dispute_id).first()
        if not dispute:
            raise ValueError(f"Dispute {esc.dispute_id} not found")

        now = datetime.now(timezone.utc)
        esc.assigned_to = assigned_to
        if esc.status == "OPEN":
            esc.status = "IN_REVIEW"
        esc.updated_at = now

        audit = AuditLog(
            dispute_id=dispute.id,
            actor=supervisor_id,
            event="ESCALATION_ASSIGNED",
            output_status="ASSIGNED",
            details_json=json.dumps({
                "escalation_id": esc.id,
                "assigned_to": assigned_to,
                "note": note,
            }),
            timestamp=now,
        )
        self.db.add(audit)
        self.db.commit()

        return SupervisorActionResponse(
            escalation_id=esc.id,
            dispute_id=dispute.id,
            action="ASSIGN",
            status=esc.status,
            message=f"Escalation assigned to {assigned_to}.",
            bridge_credit_id=None,
            timestamp=now,
        )
