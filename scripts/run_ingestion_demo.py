"""Demo script showcasing multimodal ingestion (text, voice, OCR) into AwaazLedger."""

import os
import sys
import argparse

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

scripts_dir = os.path.abspath(os.path.dirname(__file__))
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)

from app.db.session import SessionLocal
from app.services.channel_message_service import (
    process_text_message,
    process_voice_message,
    process_image_message,
)
from app.agent.state_machine import AgentOrchestrator
from seed_db import seed

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


DEMO_INGEST_CASES = [
    {
        "scenario": "SCN-01",
        "type": "TEXT (Hindi/Hinglish)",
        "user_id": 1,
        "input": "Bhaiya maine 450 rupees ka payment kiya, account se kat gaya lekin dukandar ko nahi mila. UTR 987654321012 hai.",
    },
    {
        "scenario": "SCN-01 (Voice)",
        "type": "VOICE (Sarvam Stub)",
        "user_id": 1,
        "filename": "voice_hindi_scn01.ogg",
    },
    {
        "scenario": "SCN-03 (High Value)",
        "type": "TEXT (English)",
        "user_id": 2,
        "input": "I paid INR 18,500 for flight ticket but merchant did not receive. UTR 998877665544.",
    },
    {
        "scenario": "SCN-05 (Fraud)",
        "type": "IMAGE (OCR Stub)",
        "user_id": 3,
        "filename": "screenshot_scn05_fraud.jpg",
    },
    {
        "scenario": "EDGE-01 (Ghost Success)",
        "type": "IMAGE (OCR Stub)",
        "user_id": 5,
        "filename": "screenshot_ghost_edge01.jpg",
    },
    {
        "scenario": "NO-UTR (Needs Info)",
        "type": "TEXT (Incomplete)",
        "user_id": 1,
        "input": "Mera paisa kat gaya dukandar ko nahi mila please check.",
    },
]


def run_demo(run_agent: bool = False):
    print("\nEnsuring fresh database seed data...")
    seed()

    db = SessionLocal()
    results = []

    print("\nProcessing multimodal ingestion test matrix...\n")
    for case in DEMO_INGEST_CASES:
        scn = case["scenario"]
        itype = case["type"]
        uid = case["user_id"]

        if "TEXT" in itype:
            res = process_text_message(
                sender_phone=None,
                user_id=uid,
                message=case["input"],
                channel="SIMULATOR",
                db=db,
            )
        elif "VOICE" in itype:
            res = process_voice_message(
                sender_phone=None,
                user_id=uid,
                filename=case["filename"],
                content=b"MOCK_OGG",
                channel="SIMULATOR",
                db=db,
            )
        else:
            res = process_image_message(
                sender_phone=None,
                user_id=uid,
                filename=case["filename"],
                content=b"MOCK_JPG",
                channel="SIMULATOR",
                db=db,
            )

        ent = res["entities"]
        utr = ent.utr or "N/A"
        amt = str(ent.amount) if ent.amount is not None else "N/A"
        disp_created = res["dispute_code"] if res["dispute_code"] else "NO"
        needs_info = "YES" if res["needs_more_info"] else "NO"
        agent_msg = res["agent_message"][:38] + "..." if len(res["agent_message"]) > 38 else res["agent_message"]

        agent_outcome = "N/A"
        if run_agent and res["dispute_id"]:
            orch = AgentOrchestrator(db)
            a_res = orch.run_for_dispute(res["dispute_id"])
            agent_outcome = f"{a_res['decision']} ({a_res['status']})"

        results.append({
            "scenario": scn,
            "type": itype,
            "user_id": uid,
            "utr": utr,
            "amount": amt,
            "dispute": disp_created,
            "needs_info": needs_info,
            "agent_msg": agent_msg,
            "outcome": agent_outcome,
        })

    # Print Table
    header = f"{'Scenario':<22} | {'Input Type':<20} | {'User':<5} | {'UTR':<14} | {'Amount':<8} | {'Dispute Created':<16} | {'Needs Info':<10} | {'Agent Msg Preview':<35}"
    if run_agent:
        header += f" | {'Agent Run Decision'}"
    print("=" * len(header))
    print("AwaazLedger Multimodal Ingestion Pipeline Execution Report")
    print("=" * len(header))
    print(header)
    print("-" * len(header))

    for r in results:
        row = f"{r['scenario']:<22} | {r['type']:<20} | {r['user_id']:<5} | {r['utr']:<14} | {r['amount']:<8} | {r['dispute']:<16} | {r['needs_info']:<10} | {r['agent_msg']:<35}"
        if run_agent:
            row += f" | {r['outcome']}"
        print(row)
    print("-" * len(header))

    db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run ingestion demo across modalities")
    parser.add_argument("--run-agent", action="store_true", help="Also trigger agent run for created disputes")
    args = parser.parse_args()

    run_demo(run_agent=args.run_agent)
