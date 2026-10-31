"""Paytm internal ledger mock wrapper."""

import sys
import os

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.services.paytm_ledger_client import PaytmLedgerClient


class MockPaytmLedger:
    """Wrapper around backend PaytmLedgerClient for mock-services interface."""

    def __init__(self):
        self.client = PaytmLedgerClient()

    def lookup_utr(self, utr: str):
        return self.client.query_paytm_ledger(utr=utr)


paytm_ledger_mock_instance = MockPaytmLedger()
