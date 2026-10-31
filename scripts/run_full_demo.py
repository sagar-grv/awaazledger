"""AwaazLedger Unified Master Demo Orchestrator.

Executes the complete end-to-end hackathon presentation flow across all 8 phases:
1. Database Seeding
2. Multimodal Channel Ingestion (Text, Vernacular Voice, Screenshot OCR)
3. Autonomous 3-Way Reconciliation & Agent Brain Decisioning
4. Multi-Node Regulatory Tracker Card
5. Human Supervisor Operations Desk & 1-Click Audited Actions
6. Swarm Shield Bank Switch Outage Detection
7. Merchant In-Store Sale Recovery
8. Live Fintech Telemetry & RBI Impact Metrics
"""

import os
import sys
import json
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
from app.services.channel_message_service import (
    process_text_message,
    process_voice_message,
    process_image_message,
)
from app.services.escalation_service import EscalationService
from app.services.metrics_service import MetricsService
from app.services.swarm_shield_service import SwarmShieldService
from app.services.merchant_recovery_service import MerchantRecoveryService
from app.api.disputes import _build_tracker_response
from seed_db import seed


def run_full_demo():
    print("=" * 110)
    print("  AWAAZLEDGER — AUTONOMOUS AI TEAMMATE FOR SELF-HEALING UPI DISPUTES")
    print("  Paytm Build for India AI Hackathon | Track 3: Autonomous AI Teammates")
    print("=" * 110)

    # -------------------------------------------------------------
    # PHASE 1: Seed Baseline State
    # -------------------------------------------------------------
    print("\n" + "=" * 80)
    print("  PHASE 1: Seeding Deterministic Banking & User Knowledge Base")
    print("=" * 80)
    seed()
    db = SessionLocal()

    # -------------------------------------------------------------
    # PHASE 2: Multimodal Ingestion Demo
    # -------------------------------------------------------------
    print("\n" + "=" * 80)
    print("  PHASE 2: Multimodal Channel Ingestion (Vernacular Voice, OCR & Text)")
    print("=" * 80)

    ingestion_samples = [
        ("Text (Hindi)", "+919876543210", 1, "Mera 450 kat gaya Sharma Kirana pe UTR 987654321012", "text", "SIMULATOR"),
        ("Voice (Sarvam STT)", "+919876543210", 1, "voice_hindi_scn01.ogg", "voice", "WHATSAPP"),
        ("Screenshot OCR", "+919876543214", 5, "screenshot_scn01_valid.jpg", "image", "WHATSAPP"),
        ("Fraud Ingest (OCR)", "+919876543212", 3, "screenshot_scn05_fraud.jpg", "image", "WHATSAPP"),
        ("High-Value (Text)", "+919876543211", 2, "Payment stuck of INR 18,500 for flight booking UTR 998877665544", "text", "SIMULATOR"),
    ]

    ingest_table = []
    for modality, phone, uid, payload, mtype, channel in ingestion_samples:
        try:
            if mtype == "text":
                res = process_text_message(sender_phone=phone, user_id=uid, message=payload, channel=channel, db=db)
            elif mtype == "voice":
                res = process_voice_message(sender_phone=phone, user_id=uid, filename=payload, content=b"AUDIO_RAW", channel=channel, db=db)
            else:
                res = process_image_message(sender_phone=phone, user_id=uid, filename=payload, content=b"IMAGE_RAW", channel=channel, db=db)

            code = res.get("dispute_code") or "N/A"
            entities = res.get("entities")
            utr = getattr(entities, "utr", None) or "N/A"
            amt = getattr(entities, "amount", None)
            amt_str = f"INR {amt:.2f}" if amt else "N/A"
            needs_info = "YES" if res.get("needs_more_info") else "NO"
            ingest_table.append((modality, phone, utr, amt_str, code, needs_info))
        except Exception as e:
            ingest_table.append((modality, phone, "ERROR", str(e)[:15], "ERR", "YES"))

    hdr_ingest = f"{'Modality':<20} {'Sender':<15} {'Extracted UTR':<16} {'Amount':<14} {'Dispute Code':<15} {'Needs Info'}"
    print("-" * len(hdr_ingest))
    print(hdr_ingest)
    print("-" * len(hdr_ingest))
    for row in ingest_table:
        print(f"{row[0]:<20} {row[1]:<15} {row[2]:<16} {row[3]:<14} {row[4]:<15} {row[5]}")
    print("-" * len(hdr_ingest))

    # -------------------------------------------------------------
    # PHASE 3: Autonomous Agent Brain Decisions
    # -------------------------------------------------------------
    print("\n" + "=" * 80)
    print("  PHASE 3: Autonomous Agent Brain Decisions (State Machine Loop)")
    print("=" * 80)

    orchestrator = AgentOrchestrator(db=db)
    disputes = db.query(Dispute).order_by(Dispute.id.asc()).all()

    decision_table = []
    for disp in disputes:
        res = orchestrator.run_for_dispute(disp.id)
        actions = res.get("actions_executed", [])
        act_types = [a["action_type"] for a in actions]

        has_bc = "YES" if "BRIDGE_CREDIT" in act_types else "NO"
        has_rcpt = "YES" if "GENERATE_RECEIPT" in act_types else "NO"
        has_esc = "YES" if "ESCALATE_HUMAN" in act_types else "NO"
        has_fraud = "YES" if "FRAUD_ALERT" in act_types else "NO"

        decision_table.append((
            disp.dispute_code,
            (disp.transcript or "Dispute")[:24],
            res["decision"],
            res["risk_level"],
            has_bc,
            has_rcpt,
            has_esc,
            has_fraud,
        ))

    hdr_dec = f"{'Dispute Code':<16} {'Scenario':<26} {'Decision':<16} {'Risk':<10} {'Bridge':<8} {'Receipt':<9} {'Escalate':<10} {'Fraud'}"
    print("-" * len(hdr_dec))
    print(hdr_dec)
    print("-" * len(hdr_dec))
    for row in decision_table:
        print(f"{row[0]:<16} {row[1]:<26} {row[2]:<16} {row[3]:<10} {row[4]:<8} {row[5]:<9} {row[6]:<10} {row[7]}")
    print("-" * len(hdr_dec))

    # -------------------------------------------------------------
    # PHASE 4: Multi-Node Regulatory Tracker
    # -------------------------------------------------------------
    print("\n" + "=" * 80)
    print("  PHASE 4: Multi-Node Regulatory Tracker Card (DISP-SCN-01)")
    print("=" * 80)

    disp01 = db.query(Dispute).filter(Dispute.dispute_code == "DISP-SCN-01").first()
    if disp01:
        tracker = _build_tracker_response(disp01, db)
        print(f"  Dispute Ref : {tracker['dispute_code']} | Status: {tracker['status']} | Risk: {tracker['risk_level']}")
        print(f"  Explanation : \"{tracker['explanation_user']}\"\n")
        print("  Multi-Node Progression Checkpoints:")
        for node in tracker["nodes"]:
            status_indicator = "[DONE]" if node["status"] in ("SUCCESS", "COMPLETED") else f"[{node['status']}]"
            print(f"    - {node['label']:<24}: {status_indicator:<12} ({node.get('detail', 'N/A')})")

    # -------------------------------------------------------------
    # PHASE 5: Human Supervisor Operations Desk Actions
    # -------------------------------------------------------------
    print("\n" + "=" * 80)
    print("  PHASE 5: Human Supervisor Desk (1-Click Audited Interventions)")
    print("=" * 80)

    esc_svc = EscalationService(db=db)
    queue = esc_svc.list_escalations()
    print(f"  Active Queue : {queue.open_count} open tickets awaiting supervisor review.")

    # 1. 1-Click Approve High-Value Dispute (SCN-03)
    high_val = next((i for i in queue.items if i.dispute_code == "DISP-SCN-03"), None)
    if high_val:
        print(f"\n  [ACTION 1: APPROVE] Approving Ticket #{high_val.id} ({high_val.dispute_code}) - INR {high_val.amount:.2f}")
        app_res = esc_svc.approve_escalation(
            high_val.id,
            note="Verified customer salary account and merchant terminal confirmation.",
            supervisor_id="OPS_LEAD_PRIYA",
        )
        print(f"  -> {app_res.message} (BridgeCredit #{app_res.bridge_credit_id})")

    # 2. 1-Click Request Info on Duplicate
    dup_esc = next((i for i in queue.items if "duplicate" in (i.reason or "").lower() or i.dispute_code == "DISP-SCN-EDGE-02"), None)
    if dup_esc:
        print(f"\n  [ACTION 2: REQUEST INFO] Suspicious Ticket #{dup_esc.id} ({dup_esc.dispute_code})")
        info_res = esc_svc.request_info(
            dup_esc.id,
            prompt="Please share your bank passbook scan showing the second debit timestamp.",
            supervisor_id="OPS_SUPERVISOR_MEERA",
        )
        print(f"  -> {info_res.message}")

    # 3. 1-Click Mark Fraud on Invalid UTR
    fraud_esc = next((i for i in queue.items if i.dispute_code == "DISP-SCN-05"), None)
    if fraud_esc:
        print(f"\n  [ACTION 3: MARK FRAUD] Blocking High-Risk Ticket #{fraud_esc.id} ({fraud_esc.dispute_code})")
        fr_res = esc_svc.mark_fraud(
            fraud_esc.id,
            reason="Confirmed synthetic UTR attempt across multiple device fingerprints.",
            supervisor_id="FRAUD_DESK_ANAND",
        )
        print(f"  -> {fr_res.message}")

    # -------------------------------------------------------------
    # PHASE 6: Swarm Shield Bank Outage Detection
    # -------------------------------------------------------------
    print("\n" + "=" * 80)
    print("  PHASE 6: Swarm Shield (Bank Switch Outage Cluster Detection)")
    print("=" * 80)

    # Inject 3 synthetic timeout records for SBI to demonstrate dynamic cluster detection
    now = datetime.now(timezone.utc)
    for idx in range(1, 4):
        sbi_txn = Transaction(
            utr=f"SWARM-SBI-DEMO-{idx}",
            user_id=1,
            amount=250.0 + (idx * 50),
            currency="INR",
            bank="SBI",
            status="PENDING",
            cbs_status="DEBIT_SUCCESS",
            npcI_status="U30",
            beneficiary_status="NOT_CREDITED",
            settlement_status="PENDING",
            created_at=now,
        )
        db.add(sbi_txn)
        db.flush()
        sbi_disp = Dispute(
            dispute_code=f"DISP-SWARM-DEMO-{idx}",
            user_id=1,
            transaction_id=sbi_txn.id,
            utr=sbi_txn.utr,
            amount=sbi_txn.amount,
            channel="WHATSAPP",
            intent="UPI_PENDING_DISPUTE",
            status="PENDING",
            created_at=now,
        )
        db.add(sbi_disp)
        db.commit()
        orchestrator.run_for_dispute(sbi_disp.id)

    swarm_svc = SwarmShieldService(db=db)
    swarm_report = swarm_svc.detect_active_outages()
    if swarm_report["active_outages"]:
        outage = swarm_report["active_outages"][0]
        print(f"  Active Switch Outage : {outage['bank']} ({outage['count']} cluster signals detected)")
        print(f"  Proactive Advisory   : \"{outage['advisory']}\"")
        print(f"  Dynamic Routing      : {outage['recommended_action']}")
    else:
        print("  All banking switches operational.")

    # -------------------------------------------------------------
    # PHASE 7: Merchant In-Store Sale Recovery
    # -------------------------------------------------------------
    print("\n" + "=" * 80)
    print("  PHASE 7: Merchant Sale Recovery Mini-Feature (Zero Counter Friction)")
    print("=" * 80)

    rec_svc = MerchantRecoveryService(db=db)
    if disp01:
        recovery = rec_svc.generate_recovery_payload(disp01.id)
        print(f"  Dispute Ref       : {recovery.get('dispute_code')}")
        print(f"  Recovery Link ID  : {recovery.get('merchant_recovery_id')}")
        print(f"  Dynamic QR URL    : {recovery.get('qr_url')}")
        print(f"  Collect Link      : {recovery.get('collect_link')}")
        print(f"  Merchant Message  : \"{recovery.get('merchant_message')}\"")
        print(f"  Customer Message  : \"{recovery.get('customer_message')}\"")
        print(f"  Expires At        : {recovery.get('expires_at')}")

    # -------------------------------------------------------------
    # PHASE 8: Real-Time Telemetry & Impact Metrics
    # -------------------------------------------------------------
    print("\n" + "=" * 80)
    print("  PHASE 8: Live Fintech Telemetry & RBI Impact Metrics")
    print("=" * 80)

    metrics_svc = MetricsService(db=db)
    summary = metrics_svc.get_summary()
    health = metrics_svc.get_operations_health()

    print(f"  {'Total Processed Disputes':<36}: {summary.total_disputes}")
    print(f"  {'Autonomous Resolution Rate':<36}: {summary.auto_resolution_rate_pct:.1f}%")
    print(f"  {'Total Bridge Credits Disbursed':<36}: INR {summary.bridge_credits_disbursed_inr:,.2f}")
    print(f"  {'RBI Non-Compliance Claims Saved':<36}: INR {summary.rbi_claims_saved_inr:,.2f}")
    print(f"  {'Active Bridge Credit Exposure':<36}: INR {health.active_bridge_credit_exposure_inr:,.2f}")
    print(f"  {'Average Agent Handling Time':<36}: {summary.avg_resolution_seconds:.1f} seconds")
    print(f"  {'Projected Annual L1 Cost Savings':<36}: INR {summary.projected_annual_l1_cost_savings_inr:,.2f}")
    print(f"  {'Projected TAT Reduction':<36}: {summary.projected_tat_reduction_hours:.1f} hours / ticket")

    # -------------------------------------------------------------
    # PHASE 9: Conclusion
    # -------------------------------------------------------------
    print("\n" + "=" * 110)
    print("  DEMO COMPLETE: AwaazLedger understood, verified, decided, acted, escalated safely, audited, and measured impact.")
    print("=" * 110 + "\n")


if __name__ == "__main__":
    run_full_demo()
