#!/usr/bin/env python3
"""Automated Demo Runner for AwaazLedger Voice Call AI Teammate.

Simulates vernacular voice call scenarios (Hindi, Marathi, English, DTMF, missing UTR)
through the CallDialogManager and prints real-time step-by-step resolution.
"""

import os
import sys
import json
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Ensure backend package can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.db.session import SessionLocal
from app.db.init_db import init_db
from app.services.voice_agent_service import VoiceAgentService


def run_scenario(scenario: dict):
    print("\n" + "=" * 70)
    print(f"📞 SCENARIO: {scenario['title']}")
    print(f"Language: {scenario['language'].upper()} | Caller: {scenario.get('caller_phone', 'N/A')}")
    print("=" * 70)

    db = SessionLocal()
    try:
        svc = VoiceAgentService(db)
        session = svc.initiate_call(
            caller_phone=scenario.get("caller_phone", "+918788021157"),
            channel="CLI_DEMO",
            language=scenario.get("language", "hi"),
        )
        print(f"🟢 [CALL INITIATED] Session SID: {session.call_sid}")

        # Initial Agent Greeting
        greeting = svc.start_dialog(session.call_sid)
        print(f"\n🤖 [AI AGENT] ({greeting['current_state']}):")
        print(f"   \"{greeting['agent_speech']}\"")
        if greeting.get("agent_speech_en"):
            print(f"   [English subtitle]: \"{greeting['agent_speech_en']}\"")

        for turn in scenario["turns"]:
            time.sleep(0.3)
            print("\n" + "-" * 50)
            print(f"👤 [CALLER ACTION] Step {turn['step']}: {turn['caller_action']}")
            if turn.get("caller_speech"):
                print(f"   🗣️  Caller Said: \"{turn['caller_speech']}\"")
            if turn.get("dtmf"):
                print(f"   🔢 DTMF Keypad: [{turn['dtmf']}]")

            res = svc.process_turn(
                call_sid=session.call_sid,
                transcript=turn.get("caller_speech", ""),
                dtmf_digit=turn.get("dtmf"),
            )

            print(f"\n🤖 [AI AGENT RESPONSE] (State: {res['current_state']}):")
            print(f"   \"{res['agent_speech']}\"")
            if res.get("agent_speech_en"):
                print(f"   [English subtitle]: \"{res['agent_speech_en']}\"")

            if res.get("dispute_code"):
                print(f"   🏷️  Dispute Registered: {res['dispute_code']}")
                print(f"   💰 Amount Reconciled: ₹{res.get('claimed_amount')}")
                print(f"   ⚡ Status: {res.get('dispute_status', 'RESOLVED')}")

            if res.get("is_final"):
                print(f"\n🔴 [CALL TERMINATED CLEANLY]")
                break

    finally:
        db.close()


def main():
    init_db()
    scenarios_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "mock_call_scenarios.json"))
    if not os.path.exists(scenarios_path):
        print(f"Error: {scenarios_path} not found.")
        sys.exit(1)

    with open(scenarios_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    scenarios = data.get("scenarios", [])
    print(f"\nLoaded {len(scenarios)} Voice Call AI Teammate Scenarios.")

    for sc in scenarios:
        run_scenario(sc)

    print("\n" + "=" * 70)
    print("✅ ALL VOICE CALL SCENARIOS COMPLETED SUCCESSFULLY!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
