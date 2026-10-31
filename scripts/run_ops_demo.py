"""Operations Human Supervisor Desk & Analytics Demo Script.

Demonstrates human-in-the-loop workflows, one-click audited supervisor actions,
and real-time fintech analytics aggregation for AwaazLedger.
"""

import os
import sys

# Configure UTF-8 stdout
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
scripts_dir = os.path.abspath(os.path.dirname(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)

from app.db.session import SessionLocal
from app.agent.state_machine import AgentOrchestrator
from app.services.escalation_service import EscalationService
from app.services.metrics_service import MetricsService
from app.models.dispute import Dispute
from seed_db import seed


def run_ops_demo():
    print("=" * 105)
    print("  AWAAZLEDGER — HUMAN SUPERVISOR OPERATIONS DESK & FINTECH ANALYTICS DEMO")
    print("=" * 105)

    # 1. Fresh Database Seeding
    print("\n[STEP 1] Initializing and seeding database with 5 core scenarios + 3 edge cases...")
    seed()

    db = SessionLocal()
    orchestrator = AgentOrchestrator(db=db)
    escalation_svc = EscalationService(db=db)
    metrics_svc = MetricsService(db=db)

    # 2. Run Autonomous Agent Brain on all disputes
    print("\n[STEP 2] Running Autonomous AI Teammate Brain on all seeded disputes...")
    disputes = db.query(Dispute).order_by(Dispute.id.asc()).all()
    for disp in disputes:
        orchestrator.run_for_dispute(dispute_id=disp.id)
    print(f"  -> Agent processed {len(disputes)} disputes.")

    # 3. Inspect Supervisor Queue
    print("\n[STEP 3] Fetching Supervisor Escalation Queue (Ordered by Priority + SLA)...")
    queue = escalation_svc.list_escalations()
    print(f"  Total Tickets: {queue.total} | Open/In-Review: {queue.open_count} | SLA Breached: {queue.sla_breached_count}")

    hdr = f"{'ID':<4} {'Dispute':<15} {'User':<16} {'Amount (INR)':<14} {'Priority':<10} {'Status':<14} {'Reason':<38}"
    print("-" * len(hdr))
    print(hdr)
    print("-" * len(hdr))
    for item in queue.items:
        reason_short = (item.reason or "")[:36]
        print(
            f"{item.id:<4} {item.dispute_code or 'N/A':<15} {item.user_name or 'N/A':<16} "
            f"{item.amount:<14.2f} {item.priority:<10} {item.status:<14} {reason_short:<38}"
        )
    print("-" * len(hdr))

    # 4. Demonstrate One-Click Supervisor Actions
    print("\n[STEP 4] Executing Audited Supervisor One-Click Actions:")

    # Find high-value escalation (DISP-SCN-03)
    high_val_esc = next((i for i in queue.items if i.dispute_code == "DISP-SCN-03"), None)
    if high_val_esc:
        print(f"\n  [ACTION 1: APPROVE] High-Value Escalation (Ticket #{high_val_esc.id}, {high_val_esc.dispute_code})")
        print("  AI Ceiled autonomous limit; human supervisor reviews salary slip & approves.")
        app_res = escalation_svc.approve_escalation(
            escalation_id=high_val_esc.id,
            note="Verified user KYC tier-1 and merchant terminal confirmation. Bridge credit authorized.",
            supervisor_id="OPS_LEAD_PRIYA",
        )
        print(f"  -> Status: {app_res.status} | Action: {app_res.action} | BridgeCredit ID: {app_res.bridge_credit_id}")
        print(f"  -> Message: {app_res.message}")

    # Find duplicate/edge escalation for REQUEST INFO
    dup_esc = next((i for i in queue.items if "duplicate" in (i.reason or "").lower() or i.dispute_code == "DISP-SCN-EDGE-02"), None)
    if not dup_esc:
        dup_esc = next((i for i in queue.items if i.id != high_val_esc.id), None)
    if dup_esc:
        print(f"\n  [ACTION 2: REQUEST INFO] Suspicious Ticket #{dup_esc.id} ({dup_esc.dispute_code})")
        info_res = escalation_svc.request_info(
            escalation_id=dup_esc.id,
            prompt="Please upload your bank account statement showing the second debit timestamp.",
            supervisor_id="OPS_SUPERVISOR_MEERA",
        )
        print(f"  -> Status: {info_res.status} | Action: {info_res.action}")
        print(f"  -> Message: {info_res.message}")

    # Find invalid UTR / fraud candidate for MARK FRAUD
    fraud_candidate = next((i for i in queue.items if i.dispute_code == "DISP-SCN-05" or "invalid" in (i.reason or "").lower()), None)
    if not fraud_candidate:
        fraud_candidate = next((i for i in queue.items if i.id not in (high_val_esc.id, getattr(dup_esc, 'id', None))), None)
    if fraud_candidate:
        print(f"\n  [ACTION 3: MARK FRAUD] High Risk Ticket #{fraud_candidate.id} ({fraud_candidate.dispute_code})")
        fraud_res = escalation_svc.mark_fraud(
            escalation_id=fraud_candidate.id,
            reason="Confirmed invalid UTR attempt across multiple device fingerprints.",
            supervisor_id="FRAUD_DESK_ANAND",
        )
        print(f"  -> Status: {fraud_res.status} | Action: {fraud_res.action}")
        print(f"  -> Message: {fraud_res.message}")

    # Assign remaining open ticket
    acted_ids = {high_val_esc.id, getattr(dup_esc, 'id', None), getattr(fraud_candidate, 'id', None)}
    remaining = next((i for i in queue.items if i.id not in acted_ids and i.status == "OPEN"), None)
    if not remaining:
        remaining = next((i for i in queue.items if i.status == "OPEN"), None)
    if remaining:
        print(f"\n  [ACTION 4: ASSIGN] Assigning Ticket #{remaining.id} ({remaining.dispute_code}) to L2 Investigator")
        assign_res = escalation_svc.assign_escalation(
            escalation_id=remaining.id,
            assigned_to="SUPERVISOR_SENIOR_VIKAS",
            supervisor_id="OPS_LEAD_PRIYA",
        )
        print(f"  -> Status: {assign_res.status} | Assigned To: SUPERVISOR_SENIOR_VIKAS")

    # 5. Fetch Updated Queue
    print("\n[STEP 5] Updated Supervisor Queue Status:")
    updated_queue = escalation_svc.list_escalations()
    print("-" * len(hdr))
    print(hdr)
    print("-" * len(hdr))
    for item in updated_queue.items:
        reason_short = (item.reason or "")[:36]
        print(
            f"{item.id:<4} {item.dispute_code or 'N/A':<15} {item.user_name or 'N/A':<16} "
            f"{item.amount:<14.2f} {item.priority:<10} {item.status:<14} {reason_short:<38}"
        )
    print("-" * len(hdr))

    # 6. Fetch Full Metrics Dashboard
    print("\n[STEP 6] Operations Health & Fintech Impact Analytics Summary:")
    summary = metrics_svc.get_summary()
    health = metrics_svc.get_operations_health()
    distributions = metrics_svc.get_distributions()

    print("\n" + "=" * 65)
    print("               LIVE FINTECH METRICS REPORT")
    print("=" * 65)
    print(f"  {'Total Ingested Disputes':<38}: {summary.total_disputes}")
    print(f"  {'Autonomous Resolution Rate':<38}: {summary.auto_resolution_rate_pct:.1f}%")
    print(f"  {'Auto-Resolved Disputes':<38}: {summary.auto_resolved_count}")
    print(f"  {'Total Bridge Credits Disbursed':<38}: INR {summary.bridge_credits_disbursed_inr:,.2f}")
    print(f"  {'RBI Compensation Claims Filed':<38}: {summary.rbi_claims_filed_count}")
    print(f"  {'RBI Daily Penalties Saved':<38}: INR {summary.rbi_claims_saved_inr:,.2f}")
    print(f"  {'Escalated to Human Supervisor':<38}: {summary.escalated_count}")
    print(f"  {'Currently Open Escalations':<38}: {summary.open_escalations_count}")
    print(f"  {'Fraud Claims Blocked':<38}: {summary.fraud_blocked_count}")
    print(f"  {'Avg Agent Resolution Time':<38}: {summary.avg_resolution_seconds:.1f} seconds")

    print("\n" + "-" * 65)
    print("       IMPACT BENCHMARK PROJECTIONS (SCALE ESTIMATES)")
    print("-" * 65)
    print(f"  {'Projected Annual L1 Cost Savings':<38}: INR {summary.projected_annual_l1_cost_savings_inr:,.2f}")
    print(f"  {'Projected TAT Reduction':<38}: {summary.projected_tat_reduction_hours:.1f} hours / dispute")
    print(f"  {'Estimated RBI Penalties Prevented':<38}: INR {summary.estimated_rbi_penalties_prevented_inr:,.2f}")
    print(f"  {'Impact Benchmark Version':<38}: {summary.benchmarks_version}")

    print("\n" + "-" * 65)
    print("              OPERATIONS HEALTH PANEL")
    print("-" * 65)
    print(f"  {'System Status':<38}: {health.system_status}")
    print(f"  {'Active Bridge Credit Exposure':<38}: INR {health.active_bridge_credit_exposure_inr:,.2f}")
    print(f"  {'SLA Breached Escalations':<38}: {health.sla_breached_escalations}")
    print(f"  {'Oldest Pending Ticket Age':<38}: {health.oldest_pending_hours:.1f} hours")
    print(f"  {'Avg Supervisor Resolution TAT':<38}: {health.avg_supervisor_resolution_minutes:.1f} minutes")

    print("\n" + "-" * 65)
    print("                 DISTRIBUTION BREAKDOWNS")
    print("-" * 65)
    print("  Outcomes:")
    for b in distributions.by_outcome:
        print(f"    - {b.key:<22}: {b.count:<3} ({b.percentage:.1f}%)")

    print("  Risk Levels:")
    for b in distributions.by_risk_level:
        print(f"    - {b.key:<22}: {b.count:<3} ({b.percentage:.1f}%)")

    print("  Banks:")
    for b in distributions.by_bank:
        print(f"    - {b.key:<22}: {b.count:<3} ({b.percentage:.1f}%)")

    print("=" * 65)
    print("DEMO COMPLETE: All supervisor actions audited, metrics computed live.\n")


if __name__ == "__main__":
    run_ops_demo()
