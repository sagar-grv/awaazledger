"""Sends a test inbound WhatsApp message or voice note from the user's phone to the backend webhook."""

import sys
import json
import urllib.request

def send_test_message(phone="+918788021157", text="Bhaiya 450 rupaye kat gaye, par dukandar ko nahi mila. UTR 987654321012"):
    url = "http://localhost:8000/api/v1/webhooks/whatsapp"
    clean_phone = phone.replace("+", "")

    payload = {
        "event": "messages.upsert",
        "instance": "paytm-awaazledger",
        "data": {
            "key": {
                "remoteJid": f"{clean_phone}@s.whatsapp.net",
                "id": f"TEST-MSG-{hash(text) % 100000}",
            },
            "message": {
                "conversation": text,
            },
            "messageTimestamp": 1700000000,
        },
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": "AwaazLedger-Test"},
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            print("\n[SUCCESS] Webhook accepted message from", phone)
            print("Response:", json.dumps(data, indent=2))
            return data
    except Exception as e:
        print("[ERROR] Failed to send webhook to backend:", e)
        print("Make sure the backend is running at http://localhost:8000")
        return None

if __name__ == "__main__":
    msg = sys.argv[1] if len(sys.argv) > 1 else "Bhaiya 450 rupaye kat gaye, par dukandar ko nahi mila. UTR 987654321012"
    send_test_message("+918788021157", msg)
