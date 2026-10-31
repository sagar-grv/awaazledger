"""API tests for Swarm Shield endpoint."""

from app.api.swarm import get_swarm_shield_status


def test_get_swarm_shield_endpoint(db_session):
    """Test get_swarm_shield_status returns valid response schema."""
    data = get_swarm_shield_status(db=db_session)

    assert "enabled" in data
    assert "active_outages" in data
    assert "window_minutes" in data
    assert "threshold" in data
    assert isinstance(data["active_outages"], list)
