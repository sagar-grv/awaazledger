"""Tests for PaytmLedgerClient mock service."""

from app.services.paytm_ledger_client import PaytmLedgerClient


def test_paytm_ledger_pending():
    client = PaytmLedgerClient()
    res = client.query_paytm_ledger(utr="987654321012")
    assert res["found"] is True
    assert res["settlement_status"] == "PENDING"
    assert res["merchant_credit_status"] == "NOT_CREDITED"
    assert res["soundbox_status"] == "NO_CONFIRMATION"


def test_paytm_ledger_ghost_success():
    client = PaytmLedgerClient()
    res = client.query_paytm_ledger(utr="556677889900")
    assert res["found"] is True
    assert res["settlement_status"] == "SETTLED"
    assert res["merchant_credit_status"] == "MERCHANT_CREDITED"
    assert res["soundbox_status"] == "CONFIRMED"
