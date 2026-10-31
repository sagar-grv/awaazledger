"""Unit tests for feedback aggregation in operations metrics."""

import pytest
from app.models.feedback import Feedback
from app.services.metrics_service import MetricsService


def test_metrics_feedback_aggregation(db_session):
    """Test metrics service accurately aggregates customer feedback and CSAT."""
    # Seed sample feedback records
    fb1 = Feedback(rating="HELPFUL", source="WHATSAPP")
    fb2 = Feedback(rating="HELPFUL", source="WHATSAPP")
    fb3 = Feedback(rating="NOT_HELPFUL", source="WHATSAPP")
    fb4 = Feedback(rating="WRONG_DECISION", source="WHATSAPP")
    db_session.add_all([fb1, fb2, fb3, fb4])
    db_session.commit()

    svc = MetricsService(db_session)
    summary = svc.get_summary()

    assert summary.feedback_count >= 4
    assert summary.helpful_count >= 2
    assert summary.not_helpful_count >= 1
    assert summary.wrong_decision_count >= 1
    assert 0.0 <= summary.customer_satisfaction_pct <= 100.0
