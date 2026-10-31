"""Operations human escalation queue endpoints."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.escalation_service import EscalationService
from app.schemas.escalation import (
    EscalationListResponse,
    EscalationDetailResponse,
    SupervisorActionRequest,
    SupervisorAssignRequest,
    SupervisorActionResponse,
    EscalationResolveRequest,
    EscalationResponse,
)

router = APIRouter(prefix="/escalations", tags=["Escalations"])


@router.get("", response_model=EscalationListResponse)
@router.get("/", response_model=EscalationListResponse)
def list_escalations(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    assigned_to: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """Lists human escalation tickets with priority ordering and SLA metrics."""
    service = EscalationService(db)
    return service.list_escalations(
        status=status,
        priority=priority,
        assigned_to=assigned_to,
        limit=limit,
        offset=offset,
    )


@router.get("/{escalation_id}", response_model=EscalationDetailResponse)
def get_escalation_detail(
    escalation_id: int,
    db: Session = Depends(get_db),
):
    """Returns full investigative dossier for a specific escalation ticket."""
    service = EscalationService(db)
    try:
        return service.get_escalation_detail(escalation_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{escalation_id}/approve", response_model=SupervisorActionResponse)
def approve_escalation(
    escalation_id: int,
    payload: Optional[SupervisorActionRequest] = None,
    db: Session = Depends(get_db),
):
    """Supervisor one-click approval: triggers instant bridge credit and closes ticket."""
    service = EscalationService(db)
    note = payload.note if payload else None
    supervisor_id = payload.supervisor_id if payload and payload.supervisor_id else "SUPERVISOR_L2"
    try:
        return service.approve_escalation(
            escalation_id=escalation_id,
            note=note,
            supervisor_id=supervisor_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{escalation_id}/reject", response_model=SupervisorActionResponse)
def reject_escalation(
    escalation_id: int,
    payload: Optional[SupervisorActionRequest] = None,
    db: Session = Depends(get_db),
):
    """Supervisor one-click rejection: updates dispute and notifies user."""
    service = EscalationService(db)
    reason = payload.action_reason if payload else None
    note = payload.note if payload else None
    supervisor_id = payload.supervisor_id if payload and payload.supervisor_id else "SUPERVISOR_L2"
    try:
        return service.reject_escalation(
            escalation_id=escalation_id,
            reason=reason,
            note=note,
            supervisor_id=supervisor_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{escalation_id}/request-info", response_model=SupervisorActionResponse)
def request_info_escalation(
    escalation_id: int,
    payload: Optional[SupervisorActionRequest] = None,
    db: Session = Depends(get_db),
):
    """Supervisor one-click request info: flags ticket and sends prompt to user."""
    service = EscalationService(db)
    prompt = payload.requested_info_prompt if payload else None
    note = payload.note if payload else None
    supervisor_id = payload.supervisor_id if payload and payload.supervisor_id else "SUPERVISOR_L2"
    try:
        return service.request_info(
            escalation_id=escalation_id,
            prompt=prompt,
            note=note,
            supervisor_id=supervisor_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{escalation_id}/mark-fraud", response_model=SupervisorActionResponse)
def mark_fraud_escalation(
    escalation_id: int,
    payload: Optional[SupervisorActionRequest] = None,
    db: Session = Depends(get_db),
):
    """Supervisor one-click mark fraud: blocks dispute, triggers fraud alert."""
    service = EscalationService(db)
    reason = payload.action_reason if payload else None
    note = payload.note if payload else None
    supervisor_id = payload.supervisor_id if payload and payload.supervisor_id else "SUPERVISOR_L2"
    try:
        return service.mark_fraud(
            escalation_id=escalation_id,
            reason=reason,
            note=note,
            supervisor_id=supervisor_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{escalation_id}/assign", response_model=SupervisorActionResponse)
def assign_escalation(
    escalation_id: int,
    payload: SupervisorAssignRequest,
    db: Session = Depends(get_db),
):
    """Assigns escalation to a specific human supervisor or queue."""
    service = EscalationService(db)
    try:
        return service.assign_escalation(
            escalation_id=escalation_id,
            assigned_to=payload.assigned_to,
            supervisor_id=payload.supervisor_id or "SUPERVISOR_L2",
            note=payload.note,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{escalation_id}/resolve", response_model=EscalationResponse)
def resolve_escalation(
    escalation_id: int,
    payload: EscalationResolveRequest,
    db: Session = Depends(get_db),
):
    """Legacy resolve endpoint maintained for backward compatibility."""
    service = EscalationService(db)
    if payload.approved:
        service.approve_escalation(escalation_id, note=payload.resolution_notes)
    else:
        service.reject_escalation(escalation_id, note=payload.resolution_notes)

    detail = service.get_escalation_detail(escalation_id)
    return detail.escalation
