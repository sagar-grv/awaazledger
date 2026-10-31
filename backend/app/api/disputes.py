"""Dispute lifecycle management endpoints."""

from uuid import uuid4
import os
import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.dispute import Dispute
from app.models.user import User
from app.models.transaction import Transaction
from app.models.action import Action
from app.schemas.dispute import (
    DisputeCreateRequest,
    DisputeDetailResponse,
    DisputeStatus,
    AgentDecision,
)

router = APIRouter(prefix="/disputes", tags=["Disputes"])


@router.post("/", response_model=DisputeDetailResponse)
def create_dispute(payload: DisputeCreateRequest, db: Session = Depends(get_db)):
    """Registers a new UPI payment dispute."""
    user = db.query(User).filter(User.id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"User with ID {payload.user_id} not found.")

    clean_utr = payload.utr.strip()
    if len(clean_utr) < 8 or len(clean_utr) > 32:
        raise HTTPException(status_code=400, detail="Invalid UTR format. Expected 8-32 alphanumeric characters.")

    txn = db.query(Transaction).filter(Transaction.utr == clean_utr).first()

    amount = payload.claimed_amount
    if amount is None and txn:
        amount = txn.amount
    if amount is None:
        amount = 0.0

    dispute_code = f"DISP-{uuid4().hex[:8].upper()}"

    dispute = Dispute(
        dispute_code=dispute_code,
        user_id=payload.user_id,
        transaction_id=txn.id if txn else None,
        utr=clean_utr,
        claimed_amount=payload.claimed_amount,
        amount=amount,
        channel=payload.channel,
        intent=payload.intent,
        language=payload.language,
        transcript=payload.transcript,
        ocr_json=payload.ocr_json,
        status=DisputeStatus.PENDING.value,
        agent_decision=AgentDecision.PENDING_ANALYSIS.value,
        risk_score=0.0,
        fraud_score=0.0,
        risk_level="UNKNOWN",
        confidence_score=0.95 if txn else 0.5,
        identity_verified=bool(txn and txn.user_id == payload.user_id),
    )
    db.add(dispute)
    db.commit()
    db.refresh(dispute)
    return dispute


@router.get("/", response_model=List[DisputeDetailResponse])
def list_disputes(
    status: Optional[str] = None,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """Lists disputes, optionally filtered by status or user_id."""
    query = db.query(Dispute)
    if status:
        query = query.filter(Dispute.status == status)
    if user_id:
        query = query.filter(Dispute.user_id == user_id)
    return query.order_by(Dispute.id.desc()).all()


@router.get("/{dispute_id}", response_model=DisputeDetailResponse)
def get_dispute(dispute_id: int, db: Session = Depends(get_db)):
    """Retrieves full dispute profile, including reconciliation and explanation records."""
    dispute = db.query(Dispute).filter(Dispute.id == dispute_id).first()
    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found.")
    return dispute


@router.post("/seed-demo", response_model=List[DisputeDetailResponse])
def seed_demo_disputes(db: Session = Depends(get_db)):
    """Seeds demo disputes from scenarios.json if not already present."""
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "data"))
    scenarios_file = os.path.join(data_dir, "scenarios.json")

    if not os.path.exists(scenarios_file):
        raise HTTPException(status_code=404, detail="scenarios.json not found.")

    with open(scenarios_file, "r", encoding="utf-8") as f:
        scenarios = json.load(f)

    seeded = []
    for scn in scenarios:
        code = f"DISP-{scn['scenario_id']}"
        existing = db.query(Dispute).filter(Dispute.dispute_code == code).first()
        if not existing:
            txn = db.query(Transaction).filter(Transaction.utr == scn["utr"]).first()
            user = db.query(User).filter(User.id == scn["user_id"]).first()
            disp = Dispute(
                dispute_code=code,
                user_id=scn["user_id"],
                transaction_id=txn.id if txn else None,
                utr=scn["utr"],
                claimed_amount=scn.get("claimed_amount", scn.get("amount")),
                amount=scn.get("amount", 0.0),
                channel=scn.get("channel", "SIMULATOR"),
                intent="UPI_PENDING_DISPUTE",
                language=user.language if user else "hi",
                transcript=scn["name"],
                status=DisputeStatus.PENDING.value,
                agent_decision=AgentDecision.PENDING_ANALYSIS.value,
            )
            db.add(disp)
            seeded.append(disp)

    db.commit()
    for d in seeded:
        db.refresh(d)
    return db.query(Dispute).all()


def _build_tracker_response(dispute: Dispute, db: Session) -> dict:
    three_way = {}
    if dispute.three_way_json:
        try:
            three_way = json.loads(dispute.three_way_json)
        except Exception:
            three_way = {}

    state_history = []
    if dispute.state_history_json:
        try:
            state_history = json.loads(dispute.state_history_json)
        except Exception:
            state_history = []

    actions_db = db.query(Action).filter(Action.dispute_id == dispute.id).all()
    actions_list = []
    for a in actions_db:
        p = {}
        if a.payload_json:
            try:
                p = json.loads(a.payload_json)
            except Exception:
                p = {}
        actions_list.append({
            "action_type": a.action_type,
            "status": a.status,
            "payload": p,
        })

    action_types = [a["action_type"] for a in actions_list]

    cbs_debited = three_way.get("cbs_debited")
    npcI_status = three_way.get("npcI_status")
    beneficiary_credited = three_way.get("beneficiary_credited")
    settlement_status = three_way.get("paytm_settlement_status")
    invalid_utr = three_way.get("invalid_utr", False)
    ghost_success = three_way.get("ghost_success", False)

    # 1. Remitter Bank
    if cbs_debited is True:
        node_cbs = {"label": "Remitter Bank", "status": "SUCCESS", "detail": "DEBIT_SUCCESS"}
    elif cbs_debited is False and three_way:
        node_cbs = {"label": "Remitter Bank", "status": "FAILED", "detail": "NO_DEBIT"}
    else:
        node_cbs = {"label": "Remitter Bank", "status": "PENDING", "detail": "VERIFYING"}

    # 2. NPCI Switch
    if npcI_status == "SUCCESS":
        node_npci = {"label": "NPCI Switch", "status": "SUCCESS", "detail": "SUCCESS"}
    elif npcI_status in ["U30", "BENEFICIARY_TIMEOUT", "U69"]:
        node_npci = {"label": "NPCI Switch", "status": "DELAYED", "detail": npcI_status}
    elif invalid_utr or npcI_status == "INVALID_UTR":
        node_npci = {"label": "NPCI Switch", "status": "FAILED", "detail": "INVALID_UTR"}
    elif three_way:
        node_npci = {"label": "NPCI Switch", "status": "DELAYED", "detail": npcI_status or "DELAYED"}
    else:
        node_npci = {"label": "NPCI Switch", "status": "PENDING", "detail": "PENDING"}

    # 3. Beneficiary Bank
    if beneficiary_credited is True:
        node_ben = {"label": "Beneficiary Bank", "status": "SUCCESS", "detail": "CREDITED"}
    elif beneficiary_credited is False and three_way:
        node_ben = {"label": "Beneficiary Bank", "status": "FAILED", "detail": "NOT_CREDITED"}
    else:
        node_ben = {"label": "Beneficiary Bank", "status": "PENDING", "detail": "PENDING"}

    # 4. Paytm Settlement
    if settlement_status == "SETTLED":
        node_paytm = {"label": "Paytm Settlement", "status": "SUCCESS", "detail": "SETTLED"}
    elif three_way:
        node_paytm = {"label": "Paytm Settlement", "status": "PENDING", "detail": settlement_status or "PENDING"}
    else:
        node_paytm = {"label": "Paytm Settlement", "status": "PENDING", "detail": "PENDING"}

    # 5. Bridge Credit
    if "BRIDGE_CREDIT" in action_types:
        node_bc = {"label": "Bridge Credit", "status": "SUCCESS", "detail": f"INR {dispute.amount:.2f}"}
    elif dispute.agent_decision in ["FRAUD_BLOCK", "HUMAN_ESCALATE"] or ghost_success or dispute.status in ["RECEIPT_GENERATED", "FRAUD_BLOCKED", "ESCALATED"]:
        node_bc = {"label": "Bridge Credit", "status": "NOT_APPLICABLE", "detail": "N/A"}
    else:
        node_bc = {"label": "Bridge Credit", "status": "PENDING", "detail": "PENDING"}

    # 6. RBI TAT Timer
    if "RBI_PENALTY_CLAIM" in action_types:
        node_rbi = {"label": "RBI TAT Timer", "status": "CLAIM_FILED", "detail": "Compensation Claimed"}
    elif "START_RBI_TAT_TIMER" in action_types:
        node_rbi = {"label": "RBI TAT Timer", "status": "ACTIVE", "detail": "T+1 monitoring"}
    elif dispute.agent_decision in ["FRAUD_BLOCK"] or ghost_success:
        node_rbi = {"label": "RBI TAT Timer", "status": "NOT_APPLICABLE", "detail": "N/A"}
    else:
        node_rbi = {"label": "RBI TAT Timer", "status": "NOT_STARTED", "detail": "Not required"}

    nodes = [node_cbs, node_npci, node_ben, node_paytm, node_bc, node_rbi]

    return {
        "dispute_id": dispute.id,
        "dispute_code": dispute.dispute_code,
        "utr": dispute.utr or "",
        "amount": dispute.amount,
        "status": dispute.status,
        "decision": dispute.agent_decision,
        "risk_level": dispute.risk_level or "LOW",
        "nodes": nodes,
        "actions": actions_list,
        "explanation_user": dispute.explanation_user or "",
        "explanation_internal": dispute.explanation_internal or "",
        "state_history": state_history,
    }


@router.get("/{dispute_id}/tracker")
def get_dispute_tracker(dispute_id: int, db: Session = Depends(get_db)):
    """Returns real-time multi-node dispute progression and regulatory timer statuses."""
    dispute = db.query(Dispute).filter(Dispute.id == dispute_id).first()
    if not dispute:
        raise HTTPException(status_code=404, detail=f"Dispute with ID {dispute_id} not found.")
    return _build_tracker_response(dispute, db)


@router.get("/code/{dispute_code}/tracker")
def get_dispute_tracker_by_code(dispute_code: str, db: Session = Depends(get_db)):
    """Returns tracker information queried by dispute reference code."""
    dispute = db.query(Dispute).filter(Dispute.dispute_code == dispute_code).first()
    if not dispute:
        raise HTTPException(status_code=404, detail=f"Dispute with code '{dispute_code}' not found.")
    return _build_tracker_response(dispute, db)


@router.post("/{dispute_id}/merchant-recovery")
def generate_merchant_recovery_by_id(dispute_id: int, db: Session = Depends(get_db)):
    """Generates a secure merchant sale recovery QR and collect link for a pending dispute."""
    from app.services.merchant_recovery_service import MerchantRecoveryService
    service = MerchantRecoveryService(db)
    try:
        return service.generate_recovery_payload(dispute_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/code/{dispute_code}/merchant-recovery")
def get_merchant_recovery_by_code(dispute_code: str, db: Session = Depends(get_db)):
    """Retrieves or creates a merchant sale recovery link queried by dispute reference code."""
    dispute = db.query(Dispute).filter(Dispute.dispute_code == dispute_code).first()
    if not dispute:
        raise HTTPException(status_code=404, detail=f"Dispute with code '{dispute_code}' not found.")
    from app.services.merchant_recovery_service import MerchantRecoveryService
    service = MerchantRecoveryService(db)
    return service.generate_recovery_payload(dispute.id)

