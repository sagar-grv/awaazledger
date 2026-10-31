"""API tests for Merchant Recovery endpoints."""

import pytest
from fastapi import HTTPException
from app.api.disputes import generate_merchant_recovery_by_id, get_merchant_recovery_by_code
from app.models.dispute import Dispute


def test_merchant_recovery_api_endpoints(db_session):
    """Test generating and fetching merchant recovery via dispute API handlers."""
    disp = db_session.query(Dispute).filter(Dispute.agent_decision != "FRAUD_BLOCK").first()
    assert disp is not None

    # Test generating recovery payload by dispute ID
    post_data = generate_merchant_recovery_by_id(disp.id, db=db_session)
    assert "status" in post_data

    # Test fetching recovery payload by dispute code
    get_data = get_merchant_recovery_by_code(disp.dispute_code, db=db_session)
    assert "status" in get_data


def test_merchant_recovery_not_found(db_session):
    """Test 404 on non-existent dispute ID or code."""
    with pytest.raises(HTTPException) as exc_info_id:
        generate_merchant_recovery_by_id(9999999, db=db_session)
    assert exc_info_id.value.status_code == 404

    with pytest.raises(HTTPException) as exc_info_code:
        get_merchant_recovery_by_code("DISP-NON-EXISTENT", db=db_session)
    assert exc_info_code.value.status_code == 404
