"""Transaction schemas."""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class TransactionBase(BaseModel):
    utr: str
    user_id: int
    amount: float
    currency: str = "INR"
    bank: Optional[str] = None
    merchant_id: Optional[str] = None
    merchant_name: Optional[str] = None
    merchant_vpa: Optional[str] = None
    status: str = "PENDING"
    cbs_status: str = "DEBIT_SUCCESS"
    npcI_status: str = "U30"
    beneficiary_status: str = "NOT_CREDITED"
    settlement_status: str = "PENDING"
    reversal_status: str = "NONE"


class TransactionCreate(TransactionBase):
    pass


class TransactionResponse(TransactionBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    debited_at: Optional[datetime] = None
    credited_at: Optional[datetime] = None
    created_at: datetime
