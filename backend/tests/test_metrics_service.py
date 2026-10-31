"""Tests for the fintech operations metrics service."""

import pytest
from app.models.dispute import Dispute
from app.models.bridge_credit import BridgeCredit
from app.models.rbi_claim import RbiClaim
from app.services.metrics_service import MetricsService


def test_metrics_summary_aggregation(db_session):
    service = MetricsService(db_session)
    summary = service.get_summary()

    assert summary.total_disputes >= 5
    assert summary.auto_resolution_rate_pct >= 0.0
    assert summary.benchmarks_version == "v1.0"
    assert summary.projected_tat_reduction_hours > 50.0  # 72 hrs - ~0.2 hrs


def test_metrics_distributions(db_session):
    service = MetricsService(db_session)
    distributions = service.get_distributions()

    assert len(distributions.by_bank) > 0
    assert len(distributions.by_outcome) > 0
    assert len(distributions.by_risk_level) > 0
    assert len(distributions.by_decision) > 0

    # Ensure percentages sum close to 100
    outcome_pct = sum(b.percentage for b in distributions.by_outcome)
    assert 99.0 <= outcome_pct <= 101.0


def test_operations_health(db_session):
    service = MetricsService(db_session)
    health = service.get_operations_health()

    assert health.system_status in ("HEALTHY", "ATTENTION_REQUIRED", "DEGRADED")
    assert health.open_escalations >= 0
    assert health.active_bridge_credit_exposure_inr >= 0.0


def test_metrics_dashboard(db_session):
    service = MetricsService(db_session)
    dashboard = service.get_dashboard()

    assert dashboard.summary.total_disputes >= 5
    assert len(dashboard.distributions.by_outcome) > 0
    assert dashboard.operations_health.system_status is not None
