"""Basic health endpoint test."""

from app.api.health import get_health
from app.main import app


def test_health_check():
    data = get_health()
    assert data["status"] == "healthy"
    assert data["service"] == "AwaazLedger"


def test_app_configuration():
    assert app.title == "AwaazLedger"
    assert app.version == "0.1.0"
