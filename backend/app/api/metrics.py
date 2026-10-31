"""Fintech operational metrics and SLA tracking endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.metrics_service import MetricsService
from app.schemas.metrics import (
    MetricsSummaryResponse,
    MetricsDistributionResponse,
    OperationsHealthResponse,
    MetricsDashboardResponse,
)

router = APIRouter(prefix="/metrics", tags=["Metrics"])


@router.get("/summary", response_model=MetricsSummaryResponse)
def get_metrics_summary(db: Session = Depends(get_db)):
    """Returns SLA metrics, auto-resolution rates, bridge credit totals, and cost savings."""
    service = MetricsService(db)
    return service.get_summary()


@router.get("/distributions", response_model=MetricsDistributionResponse)
def get_metrics_distributions(db: Session = Depends(get_db)):
    """Returns distribution buckets by bank, outcome, risk level, decision, and priority."""
    service = MetricsService(db)
    return service.get_distributions()


@router.get("/operations-health", response_model=OperationsHealthResponse)
def get_operations_health(db: Session = Depends(get_db)):
    """Returns real-time health indicator for supervisor operations and SLA status."""
    service = MetricsService(db)
    return service.get_operations_health()


@router.get("/dashboard", response_model=MetricsDashboardResponse)
def get_metrics_dashboard(db: Session = Depends(get_db)):
    """Returns combined analytics payload for live fintech monitoring dashboard."""
    service = MetricsService(db)
    return service.get_dashboard()


@router.get("/learning")
def get_agent_learning_metrics(db: Session = Depends(get_db)):
    """Returns autonomous self-healing, continuous learning cycles, and adaptation telemetry."""
    from app.services.learning_service import AgentLearningService
    service = AgentLearningService(db)
    return service.get_learning_telemetry()
