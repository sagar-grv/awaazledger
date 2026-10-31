"""Swarm Shield Bank Outage Cluster Detection Demo.

Demonstrates real-time cluster detection of switch-level payment timeouts (e.g., SBI U30 storm)
and automated surfacing of proactive customer advisories and UPI Lite fallback routing.
"""

import os
import sys
from datetime import datetime, timezone

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
scripts_dir = os.path.abspath(os.path.dirname(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)

from app.db.session import SessionLocal
from app.models.dispute import Dispute
from app.models.transaction import Transaction
from app.agent.state_machine import AgentOrchestrator
from app.services.swarm_shield_service import SwarmShieldService
from seed_db import seed


def run_swarm_shield_demo():
    print("=" * 85)
    print("  AWAAZLEDGER — SWARM SHIELD: BANK SWITCH OUTAGE DETECTION")
    print("=" * 85)

    print("\n[STEP 1] Initializing and seeding baseline database...")
    seed()
    db = SessionLocal()

    # Create 3 synthetic high-frequency failure transactions from SBI
    print("\n[STEP 2] Simulating incoming cluster of 3 concurrent SBI UPI timeouts...")
    synthetic_utrs = [
        ("SWARM-SBI-001", 250.0, "Mera 250 kat gaya Kirana pe SBI se"),
        ("SWARM-SBI-002", 300.0, "SBI debit ho gaya 300 par merchant ko nahi mila"),
        ("SWARM-SBI-003", 400.0, "Payment stuck on SBI UPI UTR SWARM-SBI-003"),
    ]

    orchestrator = AgentOrchestrator(db=db)
    created_disputes = []

    now = datetime.now(timezone.utc)
    for idx, (utr, amt, text) in enumerate(synthetic_utrs, 1):
        txn = Transaction(
            utr=utr,
            user_id=1,
            amount=amt,
            currency="INR",
            bank="SBI",
            merchant_name="QuickMart UPI",
            merchant_vpa="quickmart@sbi",
            status="PENDING",
            cbs_status="DEBIT_SUCCESS",
            npcI_status="U30",
            beneficiary_status="NOT_CREDITED",
            settlement_status="PENDING",
            created_at=now,
        )
        db.add(txn)
        db.flush()

        disp = Dispute(
            dispute_code=f"DISP-SWARM-0{idx}",
            user_id=1,
            transaction_id=txn.id,
            utr=utr,
            claimed_amount=amt,
            amount=amt,
            channel="WHATSAPP",
            intent="UPI_PENDING_DISPUTE",
            language="hi",
            transcript=text,
            status="PENDING",
            created_at=now,
        )
        db.add(disp)
        db.commit()

        # Run agent on each
        res = orchestrator.run_for_dispute(disp.id)
        created_disputes.append((disp, txn, res))
        print(f"  -> Processed {disp.dispute_code}: UTR={utr} | Bank=SBI | Decision={res['decision']}")

    # Step 3: Run Swarm Shield Detector
    print("\n[STEP 3] Running Swarm Shield Switch Telemetry Scanner...")
    swarm_svc = SwarmShieldService(db=db)
    result = swarm_svc.detect_active_outages()

    print(f"\n  Active Outages Detected : {len(result['active_outages'])}")
    print(f"  Monitoring Window       : {result['window_minutes']} minutes")
    print(f"  Cluster Threshold       : {result['threshold']} signals")

    if result["active_outages"]:
        print("\n" + "-" * 85)
        print("  CRITICAL SWITCH OUTAGE ADVISORY TRIGGERED:")
        print("-" * 85)
        for outage in result["active_outages"]:
            print(f"  Bank / Switch      : {outage['bank']}")
            print(f"  Signal Count       : {outage['count']} disputes in window")
            print(f"  Status             : {outage['status']}")
            print(f"  Public Advisory    : {outage['advisory']}")
            print(f"  Autonomous Action  : {outage['recommended_action']}")
        print("-" * 85)
    else:
        print("  All banking switches nominal. Zero active clusters.")

    print("\nSWARM SHIELD DEMO COMPLETE.\n")


if __name__ == "__main__":
    run_swarm_shield_demo()
