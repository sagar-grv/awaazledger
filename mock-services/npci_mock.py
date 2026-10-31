"""NPCI UDIR switch mock wrapper."""

import sys
import os

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.services.npci_client import NPCIClient


class MockNPCIUDIRSwitch:
    """Wrapper around backend NPCIClient for mock-services interface."""

    def __init__(self):
        self.client = NPCIClient()

    def query_dispute_status(self, utr: str):
        return self.client.query_npci_udir(utr=utr)


npci_mock_instance = MockNPCIUDIRSwitch()
