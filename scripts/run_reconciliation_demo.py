"""Demo script executing the Three-Way Reconciliation Engine against seeded scenarios."""

import os
import sys
import json

# Add backend directory to sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.services.reconciliation_service import ReconciliationService


def run_demo():
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
    scenarios_file = os.path.join(data_dir, "scenarios.json")

    with open(scenarios_file, "r", encoding="utf-8") as f:
        scenarios = json.load(f)

    service = ReconciliationService()

    header = (
        f"{'Scenario':<22} {'UTR':<14} {'Identity':<9} {'CBS':<6} "
        f"{'NPCI':<14} {'Beneficiary':<12} {'Duplicate':<10} {'Ghost':<7} "
        f"{'Invalid':<8} {'Signals'}"
    )
    separator = "-" * len(header)
    print("\n" + "=" * len(header))
    print("AwaazLedger -- Three-Way Reconciliation Verification Report")
    print("=" * len(header))
    print(header)
    print(separator)

    for scn in scenarios:
        res = service.reconcile(
            utr=scn["utr"],
            user_id=scn["user_id"],
            claimed_amount=scn.get("claimed_amount"),
            channel=scn.get("channel", "SIMULATOR"),
        )

        p_in = res["policy_inputs"]
        if p_in.get("fraud_block_signal"):
            signal_tag = "FRAUD_SIGNAL"
        elif res.get("ghost_success"):
            signal_tag = "RECEIPT_ONLY"
        elif p_in.get("rbi_compensation_signal"):
            signal_tag = "RBI_COMPENSATION"
        elif p_in.get("requires_human_review_signal"):
            signal_tag = "HUMAN_REVIEW"
        elif p_in.get("eligible_for_automatic_bridge_credit_signal"):
            signal_tag = "AUTO_ELIGIBLE"
        else:
            signal_tag = "REVIEW"

        name = scn["name"][:20]
        utr = res["utr"]
        ident = "true" if res["identity_match"] else "false"
        cbs = "true" if res["cbs_debited"] else "false"
        npci = (res["npcI_status"] or "UNKNOWN")[:13]
        ben = "true" if res["beneficiary_credited"] else "false"
        dup = "true" if res["duplicate_debit"] else "false"
        ghost = "true" if res["ghost_success"] else "false"
        inv = "true" if res["invalid_utr"] else "false"

        print(
            f"{name:<22} {utr:<14} {ident:<9} {cbs:<6} "
            f"{npci:<14} {ben:<12} {dup:<10} {ghost:<7} "
            f"{inv:<8} {signal_tag}"
        )

    print(separator + "\n")


if __name__ == "__main__":
    run_demo()
