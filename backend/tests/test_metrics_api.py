"""Tests for fintech operations metrics API endpoints."""

import pytest
from app.api.metrics import (
    get_metrics_summary,
    get_metrics_distributions,
    get_operations_health,
    get_metrics_dashboard,
)


def test_metrics_api_endpoints(db_session):
    summary = get_metrics_summary(db=db_session)
    assert summary.total_disputes >= 5
    assert summary.benchmarks_version == "v1.0"

    distributions = get_metrics_distributions(db=db_session)
    assert len(distributions.by_outcome) > 0

    health = get_operations_health(db=db_session)
    assert health.system_status in ("HEALTHY", "ATTENTION_REQUIRED", "DEGRADED")

    dashboard = get_metrics_dashboard(db=db_session)
    assert dashboard.summary.total_disputes == summary.total_disputes
    assert dashboard.operations_health.system_status == health.system_status
