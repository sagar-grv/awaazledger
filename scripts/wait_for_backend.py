"""Polls backend health endpoint until it is ready."""

import sys
import time
import urllib.request
import json

def wait_for_backend(url="http://localhost:8000/api/v1/health", timeout=60):
    start = time.time()
    print(f"Waiting for backend to be healthy at {url}...")
    while time.time() - start < timeout:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "AwaazLedger-HealthCheck"})
            with urllib.request.urlopen(req, timeout=3) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode())
                    print(f"Backend is ready! Status: {data.get('status')}")
                    return True
        except Exception:
            pass
        time.sleep(2)
        print(".", end="", flush=True)

    print("\n[ERROR] Backend did not respond within timeout.")
    return False

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000/api/v1/health"
    if not wait_for_backend(target):
        sys.exit(1)
