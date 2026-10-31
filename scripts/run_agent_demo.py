"""Demo script executing the Autonomous AI Teammate orchestrator across all seeded scenarios."""

import os
import sys
import json

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.db.session import SessionLocal
from app.models.dispute import Dispute
from app.models.bridge_credit import BridgeCredit
from app.models.rbi_claim import RbiClaim
from app.models.escalation import Escalation
from app.models.action import Action
from app.agent.state_machine import AgentOrchestrator


def run_agent_demo():
    db = SessionLocal()
    orchestrator = AgentOrchestrator(db=db)

    disputes = db.query(Dispute).order_by(Dispute.id.asc()).all()

    header = (
        f"{'Dispute Code':<17} {'Scenario':<24} {'UTR':<14} {'Amount':<8} "
        f"{'Decision':<15} {'Risk':<9} {'Bridge':<7} {'RBI Claim':<10} "
        f"{'Escalation':<11} {'Receipt':<8} {'Status'}"
    )
    separator = "-" * len(header)
    print("\n" + "=" * len(header))
    print("AwaazLedger — Autonomous AI Teammate Execution Report")
    print("=" * len(header))
    print(header)
    print(separator)

    scn01_result = None

    for disp in disputes:
        res = orchestrator.run_for_dispute(dispute_id=disp.id)
        if disp.dispute_code == "DISP-SCN-01":
            scn01_result = res

        # Check action executions
        actions = res.get("actions_executed", [])
        action_types = [a["action_type"] for a in actions]

        has_bridge = "YES" if "BRIDGE_CREDIT" in action_types else "NO"
        has_rbi_claim = "YES" if "RBI_PENALTY_CLAIM" in action_types else "NO"
        has_escalation = "YES" if "ESCALATE_HUMAN" in action_types else "NO"
        has_receipt = "YES" if "GENERATE_RECEIPT" in action_types else "NO"

        scenario_name = (disp.transcript or "Dispute")[:23]
        code = disp.dispute_code
        utr = disp.utr or "000000000000"
        amt = f"{disp.amount:.0f}"
        decision = res["decision"]
        risk_lvl = res["risk_level"]
        status = res["status"]

        print(
            f"{code:<17} {scenario_name:<24} {utr:<14} {amt:<8} "
            f"{decision:<15} {risk_lvl:<9} {has_bridge:<7} {has_rbi_claim:<10} "
            f"{has_escalation:<11} {has_receipt:<8} {status}"
        )

    print(separator)

    if scn01_result:
        print("\n" + "=" * 80)
        print("Detailed End-to-End JSON Response for SCN-01 (Instant Bridge Credit Flow):")
        print("=" * 80)
        print(json.dumps(scn01_result, indent=2))
        print("=" * 80 + "\n")

    db.close()


if __name__ == "__main__":
    run_agent_demo()
