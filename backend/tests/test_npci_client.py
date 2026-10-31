"""Tests for NPCIClient mock switch service."""

from app.services.npci_client import NPCIClient


def test_npci_client_pending_u30():
    client = NPCIClient()
    res = client.query_npci_udir(utr="987654321012")
    assert res["found"] is True
    assert res["npcI_status"] == "U30"
    assert res["beneficiary_credited"] is False
    assert res["auto_reversal_scheduled"] is True


def test_npci_client_ghost_success():
    client = NPCIClient()
    res = client.query_npci_udir(utr="556677889900")
    assert res["found"] is True
    assert res["npcI_status"] == "SUCCESS"
    assert res["beneficiary_credited"] is True
    assert res["auto_reversal_scheduled"] is False


def test_npci_client_invalid_utr():
    client = NPCIClient()
    res = client.query_npci_udir(utr="000000000000")
    assert res["found"] is False
    assert res["npcI_status"] == "INVALID_UTR"
    assert res["beneficiary_credited"] is False
    assert res["auto_reversal_scheduled"] is False
