"""Autonomous Agent trigger, execution, and state inspection endpoints."""

import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.dispute import Dispute
from app.schemas.agent import AgentRunResponse, AgentStateInfo
from app.agent.state_machine import AgentOrchestrator

router = APIRouter(prefix="/agent", tags=["Agent Orchestration"])


@router.post("/run/{dispute_id}", response_model=AgentRunResponse)
def run_agent_on_dispute(dispute_id: int, db: Session = Depends(get_db)):
    """Triggers the complete autonomous AI teammate resolution lifecycle for a dispute."""
    dispute = db.query(Dispute).filter(Dispute.id == dispute_id).first()
    if not dispute:
        raise HTTPException(status_code=404, detail=f"Dispute with ID {dispute_id} not found.")

    orchestrator = AgentOrchestrator(db=db)
    try:
        result = orchestrator.run_for_dispute(dispute_id=dispute.id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent orchestration failed: {str(e)}")


@router.post("/run-code/{dispute_code}", response_model=AgentRunResponse)
def run_agent_by_code(dispute_code: str, db: Session = Depends(get_db)):
    """Convenience endpoint triggering autonomous execution using dispute code."""
    dispute = db.query(Dispute).filter(Dispute.dispute_code == dispute_code).first()
    if not dispute:
        raise HTTPException(status_code=404, detail=f"Dispute code '{dispute_code}' not found.")

    orchestrator = AgentOrchestrator(db=db)
    return orchestrator.run_for_dispute(dispute_id=dispute.id)


@router.get("/state/{dispute_id}", response_model=AgentStateInfo)
def get_agent_state(dispute_id: int, db: Session = Depends(get_db)):
    """Retrieves state history and decision trail for a dispute."""
    dispute = db.query(Dispute).filter(Dispute.id == dispute_id).first()
    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found.")

    history = []
    if dispute.state_history_json:
        try:
            history = json.loads(dispute.state_history_json)
        except Exception:
            history = []

    return AgentStateInfo(
        dispute_id=dispute.id,
        current_state=dispute.status,
        history=history,
    )
