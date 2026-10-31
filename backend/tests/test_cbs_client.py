"""Tests for CBSClient mock service."""

from app.services.cbs_client import CBSClient


def test_cbs_client_valid_utr():
    client = CBSClient()
    res = client.query_bank_cbs(utr="987654321012", user_id=1)
    assert res["found"] is True
    assert res["identity_match"] is True
    assert res["cbs_status"] == "DEBIT_SUCCESS"
    assert res["amount"] == 450.0
    assert res["bank"] == "HDFC"


def test_cbs_client_invalid_utr():
    client = CBSClient()
    res = client.query_bank_cbs(utr="000000000000", user_id=1)
    assert res["found"] is False
    assert res["identity_match"] is False
    assert res["cbs_status"] == "UNKNOWN"
    assert res["amount"] is None


def test_cbs_client_user_mismatch():
    client = CBSClient()
    # Transaction 987654321012 belongs to user 1 (Rohit). Testing with user 2 (Priya)
    res = client.query_bank_cbs(utr="987654321012", user_id=2)
    assert res["found"] is True
    assert res["identity_match"] is False
