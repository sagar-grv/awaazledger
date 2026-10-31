"""Automated Evolution API Instance creation, webhook registration, and QR display."""

import os
import sys
import time
import base64
import json
from pathlib import Path

# Load settings from .env.real if available
env_real_path = Path(__file__).resolve().parent.parent / ".env.real"
env_vars = {}
if env_real_path.exists():
    with open(env_real_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env_vars[k.strip()] = v.strip().strip('"').strip("'")

EVOLUTION_API_URL = os.environ.get("EVOLUTION_SERVER_URL") or os.environ.get("EVOLUTION_API_URL") or env_vars.get("EVOLUTION_SERVER_URL") or env_vars.get("EVOLUTION_API_URL") or "http://localhost:8080"
# If localhost or docker hostname
if "evolution-api" in EVOLUTION_API_URL and not os.path.exists("/.dockerenv"):
    EVOLUTION_API_URL = "http://localhost:8080"

EVOLUTION_API_KEY = os.environ.get("EVOLUTION_API_KEY") or env_vars.get("EVOLUTION_API_KEY") or "awaazledger_secret_token_12345"
EVOLUTION_INSTANCE_NAME = os.environ.get("EVOLUTION_INSTANCE_NAME") or env_vars.get("EVOLUTION_INSTANCE_NAME") or "paytm-awaazledger"
EVOLUTION_WEBHOOK_URL = os.environ.get("EVOLUTION_WEBHOOK_URL") or env_vars.get("EVOLUTION_WEBHOOK_URL") or "http://backend:8000/api/v1/webhooks/whatsapp"


def wait_for_evolution(url, api_key, timeout=40):
    import urllib.request
    start = time.time()
    print(f"Checking Evolution API status at {url}...")
    headers = {"apikey": api_key, "User-Agent": "AwaazLedger-Setup"}
    while time.time() - start < timeout:
        try:
            req = urllib.request.Request(f"{url}/instance/fetchInstances", headers=headers)
            with urllib.request.urlopen(req, timeout=3) as resp:
                if resp.status in (200, 201):
                    print("Evolution API is online and responding.")
                    return True
        except Exception:
            pass
        time.sleep(2)
        print(".", end="", flush=True)
    print("\n[WARN] Evolution API not responding yet or unauthenticated.")
    return False


def setup_instance():
    try:
        import httpx
    except ImportError:
        print("[ERROR] httpx is required. Install via pip install httpx.")
        return False

    print(f"\nSetting up Evolution WhatsApp Instance: '{EVOLUTION_INSTANCE_NAME}'")
    headers = {
        "apikey": EVOLUTION_API_KEY,
        "Content-Type": "application/json",
    }

    client = httpx.Client(timeout=15.0)

    # 1. Check existing instances
    instance_exists = False
    try:
        resp = client.get(f"{EVOLUTION_API_URL}/instance/fetchInstances", headers=headers)
        if resp.status_code == 200:
            instances = resp.json()
            if isinstance(instances, list):
                for inst in instances:
                    name = inst.get("instance", {}).get("instanceName") or inst.get("name")
                    if name == EVOLUTION_INSTANCE_NAME:
                        instance_exists = True
                        break
    except Exception as e:
        print(f"Could not fetch instances: {e}")

    # 2. Create instance if not exists
    qr_data = None
    if not instance_exists:
        print(f"Creating new instance '{EVOLUTION_INSTANCE_NAME}' with webhook -> {EVOLUTION_WEBHOOK_URL}")
        create_payload = {
            "instanceName": EVOLUTION_INSTANCE_NAME,
            "qrcode": True,
            "integration": "WHATSAPP-BAILEYS",
            "webhook": {
                "enabled": True,
                "url": EVOLUTION_WEBHOOK_URL,
                "events": ["messages.upsert"],
                "base64": True,
                "byEvents": False,
            },
            "qrcode": {
                "limit": 1,
                "delay": 0,
            },
        }
        try:
            res = client.post(f"{EVOLUTION_API_URL}/instance/create", headers=headers, json=create_payload)
            if res.status_code in (200, 201):
                body = res.json()
                qr_data = (body.get("qrcode") or {}).get("base64") or body.get("base64") or body.get("code")
                print("Instance created successfully.")
            else:
                print(f"Instance create returned: {res.status_code} {res.text}")
        except Exception as e:
            print(f"Failed to create instance: {e}")
    else:
        print(f"Instance '{EVOLUTION_INSTANCE_NAME}' already exists. Updating webhook configuration...")
        webhook_payload = {
            "enabled": True,
            "url": EVOLUTION_WEBHOOK_URL,
            "events": ["messages.upsert"],
            "base64": True,
        }
        try:
            client.post(f"{EVOLUTION_API_URL}/webhook/set/{EVOLUTION_INSTANCE_NAME}", headers=headers, json=webhook_payload)
        except Exception as e:
            print(f"Webhook update note: {e}")

    # 3. Fetch current QR code if not already captured
    if not qr_data:
        try:
            res = client.get(f"{EVOLUTION_API_URL}/instance/connect/{EVOLUTION_INSTANCE_NAME}", headers=headers)
            if res.status_code in (200, 201):
                body = res.json()
                qr_data = body.get("base64") or body.get("code") or (body.get("qrcode") or {}).get("base64")
        except Exception as e:
            print(f"Could not connect instance: {e}")

    # 4. Save and display QR
    dist_dir = Path(__file__).resolve().parent.parent / "dist"
    dist_dir.mkdir(parents=True, exist_ok=True)
    qr_file = dist_dir / "evolution_qr.png"

    if qr_data:
        # Check if base64 data URL
        b64_str = qr_data
        if "base64," in b64_str:
            b64_str = b64_str.split("base64,")[1]

        try:
            img_bytes = base64.b64decode(b64_str)
            with open(qr_file, "wb") as f:
                f.write(img_bytes)
            print(f"\n[SUCCESS] QR Code saved to: {qr_file}")
        except Exception:
            # If qr_data is raw text pairing code
            try:
                import qrcode
                img = qrcode.make(qr_data)
                img.save(str(qr_file))
                print(f"\n[SUCCESS] Generated QR image saved to: {qr_file}")
            except Exception:
                pass

        # Try printing ASCII QR in terminal
        try:
            import qrcode
            qr = qrcode.QRCode()
            qr.add_data(qr_data)
            print("\nSCAN THIS QR CODE WITH WHATSAPP ON YOUR PHONE:")
            qr.print_ascii(invert=True)
        except Exception:
            print("\nTo scan the QR code, open the saved image:")
            print(f" -> {qr_file}")
    else:
        print("\nInstance may already be connected or QR not required. Check dashboard.")

    print("\n-------------------------------------------------------------")
    print("INSTRUCTIONS TO LINK WHATSAPP:")
    print("1. Open WhatsApp on your phone.")
    print("2. Go to Settings -> Linked Devices -> Link a Device.")
    print("3. Scan the QR code displayed above or open dist/evolution_qr.png.")
    print("4. When connected, send a message to this number!")
    print("-------------------------------------------------------------\n")
    return True


if __name__ == "__main__":
    wait_for_evolution(EVOLUTION_API_URL, EVOLUTION_API_KEY, timeout=10)
    setup_instance()
