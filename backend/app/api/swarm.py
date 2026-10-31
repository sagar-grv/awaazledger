"""Swarm Shield bank outage advisory endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.swarm_shield_service import SwarmShieldService

router = APIRouter(tags=["Swarm Shield"])


@router.get("/swarm-shield")
def get_swarm_shield_status(db: Session = Depends(get_db)):
    """Returns active bank-level switch outages and proactive UPI Lite fallback advisories."""
    service = SwarmShieldService(db)
    return service.detect_active_outages()
