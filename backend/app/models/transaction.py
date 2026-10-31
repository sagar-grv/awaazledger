"""Transaction database model."""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from app.db.base import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    utr = Column(String(64), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="INR")
    bank = Column(String(50), nullable=True)
    merchant_id = Column(String(64), nullable=True)
    merchant_name = Column(String(100), nullable=True)
    merchant_vpa = Column(String(100), nullable=True)
    status = Column(String(32), default="PENDING")
    cbs_status = Column(String(32), default="DEBIT_SUCCESS")  # DEBIT_SUCCESS / DEBIT_FAILED / UNKNOWN
    npcI_status = Column(String(32), default="U30")  # SUCCESS / U30 / U69 / INVALID_UTR / BENEFICIARY_TIMEOUT / DEEMED_APPROVED
    beneficiary_status = Column(String(32), default="NOT_CREDITED")  # CREDITED / NOT_CREDITED / TIMEOUT / UNKNOWN
    settlement_status = Column(String(32), default="PENDING")  # SETTLED / PENDING / FAILED / IN_TRANSIT
    debited_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    credited_at = Column(DateTime, nullable=True)
    reversal_status = Column(String(32), default="NONE")  # NONE / SCHEDULED / COMPLETED / FAILED
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
