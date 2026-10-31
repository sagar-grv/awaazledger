"""Unit tests for Swarm Shield bank switch outage detection service."""

from datetime import datetime, timezone
import pytest
from app.services.swarm_shield_service import SwarmShieldService
from app.models.dispute import Dispute
from app.models.transaction import Transaction
from app.models.user import User
from app.core.config import settings


def test_swarm_shield_enabled(db_session):
    """Test Swarm Shield service returns structured result when enabled."""
    svc = SwarmShieldService(db_session)
    res = svc.detect_active_outages()

    assert "enabled" in res
    assert "active_outages" in res
    assert "window_minutes" in res
    assert "threshold" in res
    assert isinstance(res["active_outages"], list)


def test_swarm_shield_disabled(monkeypatch, db_session):
    """Test Swarm Shield returns disabled response when feature flag is off."""
    monkeypatch.setattr(settings, "ENABLE_SWARM_SHIELD", False)
    svc = SwarmShieldService(db_session)
    res = svc.detect_active_outages()

    assert res["enabled"] is False
    assert res["active_outages"] == []


def test_swarm_shield_outage_detection_with_clusters(db_session):
    """Test detecting bank switch outages when threshold is met."""
    # Create synthetic user and 3 transactions with NPCI timeouts for TEST_BANK
    user = db_session.query(User).first()
    now = datetime.now(timezone.utc)

    for i in range(3):
        txn = Transaction(
            user_id=user.id,
            utr=f"99990000000{i}",
            amount=500.0,
            merchant_name="Test Mart",
            bank="AXIS",
            cbs_status="DEBIT_SUCCESS",
            npcI_status="U30",
            status="PENDING",
            beneficiary_status="TIMEOUT",
            created_at=now,
        )
        db_session.add(txn)
        db_session.flush()

        disp = Dispute(
            dispute_code=f"DISP-AXIS-{i}",
            user_id=user.id,
            transaction_id=txn.id,
            status="PENDING_VERIFICATION",
            agent_decision="PENDING",
            three_way_json='{"npci_status": "U30"}',
            created_at=now,
        )
        db_session.add(disp)

    db_session.commit()

    svc = SwarmShieldService(db_session)
    res = svc.detect_active_outages()

    assert res["enabled"] is True
    # Verify AXIS bank is identified in recent signal counts
    assert "AXIS" in res["recent_signal_counts"]
    assert res["recent_signal_counts"]["AXIS"] >= 3

    # Check that active outages contains AXIS
    axis_outage = next((o for o in res["active_outages"] if o["bank"] == "AXIS"), None)
    assert axis_outage is not None
    assert axis_outage["status"] == "ACTIVE"
    assert "AXIS" in axis_outage["advisory"]
    assert axis_outage["recommended_action"] == "ROUTE_UPI_LITE_FALLBACK"
