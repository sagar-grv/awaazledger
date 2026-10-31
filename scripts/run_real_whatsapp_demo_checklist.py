"""Diagnostic pre-flight checklist for Real WhatsApp + Sarvam AI demo mode."""

import os
import sys
import subprocess
import urllib.request
import json
from pathlib import Path


def check_docker():
    try:
        res = subprocess.run(["docker", "info"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)
        return res.returncode == 0
    except Exception:
        return False


def check_url(url, timeout=3):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "AwaazLedger-Diagnostic"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status == 200:
                return json.loads(resp.read().decode())
    except Exception:
        pass
    return None


def run_checklist():
    print("=" * 70)
    print("  AWAAZLEDGER — REAL WHATSAPP + SARVAM DEMO PRE-FLIGHT CHECKLIST")
    print("=" * 70)

    # 1. Docker
    docker_ok = check_docker()
    print(f"[{'PASS' if docker_ok else 'WARN'}] Docker Engine Running: {docker_ok}")

    # 2. Backend Health
    backend_health = check_url("http://localhost:8000/api/v1/health")
    backend_ok = backend_health is not None
    print(f"[{'PASS' if backend_ok else 'FAIL'}] Backend API (http://localhost:8000): {backend_ok}")

    # 3. Webhook Health
    webhook_health = check_url("http://localhost:8000/api/v1/webhooks/whatsapp/health")
    if webhook_health:
        print(f"[PASS] Webhook Diagnostic Engine: HEALTHY")
        print(f"       - Mode: {webhook_health.get('whatsapp_mode')}")
        print(f"       - Evolution Live: {webhook_health.get('evolution_live')}")
        print(f"       - Sarvam Real: {webhook_health.get('sarvam_real')}")
        print(f"       - OCR Real: {webhook_health.get('ocr_real')}")
        print(f"       - Feedback Enabled: {webhook_health.get('feedback_enabled')}")
    else:
        print(f"[WARN] Webhook Endpoint: Not responding (Start backend first)")

    # 4. Evolution API
    evolution_ok = False
    try:
        req = urllib.request.Request("http://localhost:8080", headers={"User-Agent": "AwaazLedger"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            evolution_ok = resp.status in (200, 404, 401)
    except Exception:
        pass
    print(f"[{'PASS' if evolution_ok else 'WARN'}] Evolution API Gateway (http://localhost:8080): {evolution_ok}")

    # 5. QR Code File
    dist_qr = Path(__file__).resolve().parent.parent / "dist" / "evolution_qr.png"
    print(f"[{'PASS' if dist_qr.exists() else 'INFO'}] WhatsApp QR File ({dist_qr.name}): {'Present' if dist_qr.exists() else 'Run setup_evolution_instance.py'}")

    # 6. Phone User Map
    data_map = Path(__file__).resolve().parent.parent / "data" / "phone_user_map.json"
    print(f"[{'PASS' if data_map.exists() else 'FAIL'}] Phone Mapping Registry: {'Present' if data_map.exists() else 'Missing'}")

    print("=" * 70)
    print("DEMO URLS:")
    print(" - WhatsApp Simulator & Demo : http://localhost:5173")
    print(" - Human Supervisor Desk      : http://localhost:5173/dashboard")
    print(" - Fintech Telemetry & CSAT   : http://localhost:5173/metrics")
    print(" - Backend OpenAPI Docs       : http://localhost:8000/docs")
    print("=" * 70)

    if not backend_ok or not docker_ok:
        print("\nTo start all services in Docker with one command, run:")
        print(" -> .\\scripts\\start_real_demo.ps1  (Windows)")
        print(" -> ./scripts/start_real_demo.sh    (Linux/macOS)")
    else:
        print("\nAll systems are primed and ready for real WhatsApp testing!")

    return 0


if __name__ == "__main__":
    sys.exit(run_checklist())
