"""Test configuration and fixtures for AwaazLedger tests."""

import os
import sys
import pytest

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

scripts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)

from seed_db import seed
from app.db.session import SessionLocal


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Ensure database has fresh seed data before running test suite."""
    seed()
    yield


@pytest.fixture
def db_session():
    """Provides a transactional database session for tests."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
