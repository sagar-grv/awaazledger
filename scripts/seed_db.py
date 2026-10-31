"""Database seed script populating realistic mock users, transactions, and disputes."""

import os
import sys
import json
from datetime import datetime, timezone, timedelta

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.db.session import SessionLocal, engine
from app.db.base import Base
from app.models.user import User
from app.models.transaction import Transaction
from app.models.dispute import Dispute
from app.schemas.dispute import DisputeStatus, AgentDecision


def seed():
    print("Dropping existing tables and recreating schema...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))

    # 1. Seed Users
    users_file = os.path.join(data_dir, "users.json")
    with open(users_file, "r", encoding="utf-8") as f:
        users_data = json.load(f)

    for u in users_data:
        user = User(
            id=u.get("id"),
            name=u["name"],
            mobile_hash=u["mobile_hash"],
            paytm_id=u["paytm_id"],
            language=u.get("language", "hi"),
            trust_score=u.get("trust_score", 100),
            kyc_status=u.get("kyc_status", "VERIFIED"),
            device_id=u.get("device_id"),
            blacklisted=u.get("blacklisted", False),
            previous_dispute_count=u.get("previous_dispute_count", 0),
        )
        db.add(user)
    db.commit()
    print(f"Seeded {len(users_data)} users.")

    # 2. Seed Transactions
    txns_file = os.path.join(data_dir, "transactions.json")
    with open(txns_file, "r", encoding="utf-8") as f:
        txns_data = json.load(f)

    now = datetime.now(timezone.utc)

    for t in txns_data:
        if t.get("days_ago"):
            debited_time = now - timedelta(days=t["days_ago"])
        elif t.get("offset_seconds"):
            debited_time = now - timedelta(seconds=t["offset_seconds"])
        else:
            debited_time = now - timedelta(minutes=5)

        txn = Transaction(
            id=t.get("id"),
            utr=t["utr"],
            user_id=t["user_id"],
            amount=t["amount"],
            currency=t.get("currency", "INR"),
            bank=t.get("bank"),
            merchant_id=t.get("merchant_id"),
            merchant_name=t.get("merchant_name"),
            merchant_vpa=t.get("merchant_vpa"),
            status=t.get("status", "PENDING"),
            cbs_status=t.get("cbs_status", "DEBIT_SUCCESS"),
            npcI_status=t.get("npcI_status", "U30"),
            beneficiary_status=t.get("beneficiary_status", "NOT_CREDITED"),
            settlement_status=t.get("settlement_status", "PENDING"),
            debited_at=debited_time,
            reversal_status=t.get("reversal_status", "NONE"),
        )
        db.add(txn)
    db.commit()
    print(f"Seeded {len(txns_data)} transactions.")

    # 3. Seed Demo Disputes
    scenarios_file = os.path.join(data_dir, "scenarios.json")
    with open(scenarios_file, "r", encoding="utf-8") as f:
        scenarios = json.load(f)

    disputes_seeded = 0
    for scn in scenarios:
        code = f"DISP-{scn['scenario_id']}"
        existing = db.query(Dispute).filter(Dispute.dispute_code == code).first()
        if not existing:
            txn = db.query(Transaction).filter(Transaction.utr == scn["utr"]).first()
            user = db.query(User).filter(User.id == scn["user_id"]).first()
            amount = scn.get("claimed_amount") or scn.get("amount") or (txn.amount if txn else 0.0)

            disp = Dispute(
                dispute_code=code,
                user_id=scn["user_id"],
                transaction_id=txn.id if txn else None,
                utr=scn["utr"],
                claimed_amount=scn.get("claimed_amount", amount),
                amount=amount,
                channel=scn.get("channel", "SIMULATOR"),
                intent="UPI_PENDING_DISPUTE",
                language=user.language if user else "hi",
                transcript=scn["name"],
                status=DisputeStatus.PENDING.value,
                agent_decision=AgentDecision.PENDING_ANALYSIS.value,
            )
            db.add(disp)
            disputes_seeded += 1

    db.commit()
    print(f"Seeded {disputes_seeded} disputes.")

    db.close()
    print("Database seeding completed successfully.")


if __name__ == "__main__":
    seed()
