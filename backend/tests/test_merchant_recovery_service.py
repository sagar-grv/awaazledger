"""Unit tests for Merchant Recovery service."""

from datetime import datetime, timezone
import pytest
from app.services.merchant_recovery_service import MerchantRecoveryService
from app.models.dispute import Dispute
from app.models.transaction import Transaction
from app.models.user import User
from app.models.action import Action
from app.models.audit_log import AuditLog
from app.core.config import settings


def test_merchant_recovery_generation_success(db_session):
    """Test generating recovery payload for eligible auto-credited dispute."""
    user = db_session.query(User).first()
    txn = Transaction(
        user_id=user.id,
        utr="888877776666",
        amount=650.0,
        merchant_name="Corner Kirana",
        bank="HDFC",
        cbs_status="DEBIT_SUCCESS",
        npcI_status="PENDING",
        status="PENDING",
        beneficiary_status="NOT_CREDITED",
    )
    db_session.add(txn)
    db_session.flush()

    dispute = Dispute(
        dispute_code="DISP-REC-01",
        user_id=user.id,
        transaction_id=txn.id,
        status="AUTO_CREDITED",
        agent_decision="AUTO_BRIDGE_CREDIT",
    )
    db_session.add(dispute)
    db_session.commit()

    svc = MerchantRecoveryService(db_session)
    res = svc.generate_recovery_payload(dispute.id)

    assert res["status"] == "RECOVERY_LINK_GENERATED"
    assert "merchant_recovery_id" in res
    assert "qr_url" in res
    assert "collect_link" in res
    assert "fallback_options" in res
    assert res["dispute_code"] == "DISP-REC-01"

    # Verify Action created in DB
    action = (
        db_session.query(Action)
        .filter(Action.dispute_id == dispute.id, Action.action_type == "MERCHANT_RECOVERY_LINK")
        .first()
    )
    assert action is not None
    assert action.status == "COMPLETED"

    # Verify AuditLog created
    audit = (
        db_session.query(AuditLog)
        .filter(AuditLog.dispute_id == dispute.id, AuditLog.event == "MERCHANT_RECOVERY_GENERATED")
        .first()
    )
    assert audit is not None


def test_merchant_recovery_idempotency(db_session):
    """Test that second call returns cached recovery payload."""
    dispute = db_session.query(Dispute).filter(Dispute.dispute_code == "DISP-REC-01").first()
    assert dispute is not None

    svc = MerchantRecoveryService(db_session)
    res1 = svc.generate_recovery_payload(dispute.id)
    res2 = svc.generate_recovery_payload(dispute.id)

    assert res1["merchant_recovery_id"] == res2["merchant_recovery_id"]
    assert res1["qr_url"] == res2["qr_url"]


def test_merchant_recovery_fraud_blocked_ineligible(db_session):
    """Test that fraud blocked dispute is not eligible for recovery link."""
    user = db_session.query(User).first()
    txn = Transaction(
        user_id=user.id,
        utr="000011112222",
        amount=1999.0,
        merchant_name="Shady Deals",
        bank="SBI",
        cbs_status="NOT_FOUND",
        npcI_status="INVALID_UTR",
        status="FAILED",
    )
    db_session.add(txn)
    db_session.flush()

    dispute = Dispute(
        dispute_code="DISP-REC-FRAUD",
        user_id=user.id,
        transaction_id=txn.id,
        status="FRAUD_BLOCKED",
        agent_decision="FRAUD_BLOCK",
    )
    db_session.add(dispute)
    db_session.commit()

    svc = MerchantRecoveryService(db_session)
    res = svc.generate_recovery_payload(dispute.id)

    assert res["status"] == "NOT_ELIGIBLE"


def test_merchant_recovery_ghost_success(db_session):
    """Test that ghost-success dispute returns already available receipt notice."""
    user = db_session.query(User).first()
    txn = Transaction(
        user_id=user.id,
        utr="333344445555",
        amount=300.0,
        merchant_name="Reliance Fresh",
        bank="ICICI",
        cbs_status="DEBIT_SUCCESS",
        npcI_status="SUCCESS",
        status="PENDING",
        beneficiary_status="CREDITED",
    )
    db_session.add(txn)
    db_session.flush()

    dispute = Dispute(
        dispute_code="DISP-REC-GHOST",
        user_id=user.id,
        transaction_id=txn.id,
        status="RECEIPT_GENERATED",
        agent_decision="GHOST_SUCCESS_RECEIPT",
    )
    db_session.add(dispute)
    db_session.commit()

    svc = MerchantRecoveryService(db_session)
    res = svc.generate_recovery_payload(dispute.id)

    assert res["status"] == "RECEIPT_ALREADY_AVAILABLE"
