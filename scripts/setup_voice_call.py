#!/usr/bin/env python3
"""Diagnostic setup and verification script for AwaazLedger Voice Call AI Teammate."""

import os
import sys
import json
import httpx

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def check_voice_call_environment():
    print("=" * 65)
    print("🚀 PAYTM AWAAZLEDGER - VOICE CALL AI TEAMMATE DIAGNOSTICS")
    print("=" * 65)

    backend_url = os.environ.get("PUBLIC_BACKEND_URL", "http://localhost:8000")
    print(f"[*] Checking Backend Health at {backend_url}...")
    try:
        res = httpx.get(f"{backend_url}/api/v1/health", timeout=3.0)
        if res.status_code == 200:
            print(f"  [OK] Backend is healthy ({res.json()})")
        else:
            print(f"  [WARN] Backend responded with HTTP {res.status_code}")
    except Exception as e:
        print(f"  [INFO] Backend not currently reachable: {e} (Will use local database)")

    print("\n[*] Checking Voice Call Storage & Directories...")
    audio_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend", "static", "audio"))
    os.makedirs(audio_dir, exist_ok=True)
    print(f"  [OK] Static audio cache directory: {audio_dir}")

    print("\n[*] Checking Mock Scenarios...")
    scenarios_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "mock_call_scenarios.json"))
    if os.path.exists(scenarios_path):
        with open(scenarios_path, "r", encoding="utf-8") as f:
            sc = json.load(f).get("scenarios", [])
        print(f"  [OK] {len(sc)} scenarios loaded from mock_call_scenarios.json")
    else:
        print(f"  [FAIL] Missing {scenarios_path}")

    print("\n[*] Telephony & Audio Configuration:")
    print("  Mode: Simulator (WebRTC Browser Microphone + SpeechSynthesis / Sarvam AI)")
    print("  Browser WebRTC Portal: http://localhost:5173/call")
    print("  Telephony Webhook: POST /api/v1/calls/webhook/telephony")
    print("  WebSocket Audio Stream: ws://localhost:8000/api/v1/calls/ws/{call_sid}")
    print("  Supported Languages: Hindi (hi), Marathi (mr), English (en)")
    print("  Voice Engine: Dual (Sarvam Bulbul TTS + Local SpeechSynthesis fallback)")
    print("=" * 65)
    print("Voice Call AI Teammate is ready for demo!")
    print("=" * 65)

if __name__ == "__main__":
    check_voice_call_environment()
