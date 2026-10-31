"""Unit tests for Three-Way Reconciliation Engine."""

from app.services.reconciliation_service import ReconciliationService


def test_scn_01_valid_pending_small_ticket():
    service = ReconciliationService()
    res = service.reconcile(utr="987654321012", user_id=1, claimed_amount=450.0)

    assert res["identity_match"] is True
    assert res["cbs_debited"] is True
    assert res["beneficiary_credited"] is False
    assert res["invalid_utr"] is False
    assert res["duplicate_debit"] is False
    assert res["ghost_success"] is False
    assert res["amount_matches"] is True
    assert res["policy_inputs"]["eligible_for_automatic_bridge_credit_signal"] is True
    assert res["policy_inputs"]["requires_human_review_signal"] is False
    assert res["policy_inputs"]["fraud_block_signal"] is False


def test_scn_03_high_value_escalation():
    service = ReconciliationService()
    res = service.reconcile(utr="998877665544", user_id=2, claimed_amount=18500.0)

    assert res["cbs_debited"] is True
    assert res["beneficiary_credited"] is False
    assert res["cbs_amount"] == 18500.0
    assert res["policy_inputs"]["eligible_for_automatic_bridge_credit_signal"] is False
    assert res["policy_inputs"]["requires_human_review_signal"] is True
    assert any("exceeds autonomous ceiling" in r for r in res["policy_inputs"]["reasons"])


def test_scn_05_invalid_utr():
    service = ReconciliationService()
    res = service.reconcile(utr="000000000000", user_id=3, claimed_amount=1999.0)

    assert res["invalid_utr"] is True
    assert res["cbs_found"] is False
    assert res["npcI_found"] is False
    assert res["policy_inputs"]["fraud_block_signal"] is True
    assert res["policy_inputs"]["eligible_for_automatic_bridge_credit_signal"] is False


def test_ghost_success_receipt_only():
    service = ReconciliationService()
    res = service.reconcile(utr="556677889900", user_id=5, claimed_amount=780.0)

    assert res["ghost_success"] is True
    assert res["cbs_debited"] is True
    assert res["beneficiary_credited"] is True
    assert res["policy_inputs"]["eligible_for_automatic_bridge_credit_signal"] is False
    assert any("receipt" in r.lower() for r in res["policy_inputs"]["reasons"])


def test_duplicate_debit_detection():
    service = ReconciliationService()
    # Transaction 778899001123 occurred within 20s of 778899001122 for same user and merchant
    res = service.reconcile(utr="778899001123", user_id=4, claimed_amount=650.0)

    assert res["duplicate_debit"] is True
    assert "778899001122" in res["duplicate_utrs"]
    assert res["policy_inputs"]["requires_human_review_signal"] is True


def test_amount_mismatch_detection():
    service = ReconciliationService()
    # UTR 334455667788 is for INR 500 in CBS, but user claims INR 5000 (severe mismatch > max(100, 10%))
    res = service.reconcile(utr="334455667788", user_id=2, claimed_amount=5000.0)

    assert res["amount_mismatch"] is True
    assert res["amount_matches"] is False
    assert res["policy_inputs"]["fraud_block_signal"] is True
    assert any("amount mismatch" in r.lower() for r in res["policy_inputs"]["reasons"])
