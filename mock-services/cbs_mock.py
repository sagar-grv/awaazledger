"""Core Banking System (CBS) mock wrapper."""

import sys
import os

# Add backend directory to sys.path if not present
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.services.cbs_client import CBSClient


class MockCoreBankingSystem:
    """Wrapper around backend CBSClient for mock-services interface."""

    def __init__(self):
        self.client = CBSClient()

    def verify_debit(self, account_no: str, utr: str):
        return self.client.query_bank_cbs(utr=utr)


cbs_mock_instance = MockCoreBankingSystem()
