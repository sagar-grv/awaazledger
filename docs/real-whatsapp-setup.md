# AwaazLedger — Real WhatsApp & Sarvam AI Production Guide

**Paytm Build for India AI Hackathon | Track 3: Autonomous AI Teammates**  
*Operating Mode: Real WhatsApp (Evolution API) + Real Sarvam AI STT/TTS + Mock Banking SQLite Truth Layer*

---

## 🌟 Architecture Overview

```text
Real WhatsApp User (You / Judge)
            │
            ▼ (Text / Vernacular Voice Note / Receipt Screenshot)
Evolution API (Running in Docker :8080)
            │
            ▼ Webhook (POST http://backend:8000/api/v1/webhooks/whatsapp)
AwaazLedger FastAPI Backend (:8000)
    ├── 1. Ingestion & Normalization (WhatsApp Adapter)
    ├── 2. Multimodal Extraction (Real Sarvam AI STT / Tesseract OCR / Fallback)
    ├── 3. Phone Mapping (DEMO_WHATSAPP_NUMBER or phone_user_map.json)
    ├── 4. Financial Truth Reconciler (Mock CBS ↔ NPCI UDIR ↔ Paytm Ledger)
    ├── 5. Risk & Deterministic Policy Engine (Zero LLM Financial Hallucination)
    ├── 6. Action Execution (Provisional Bridge Credit, Receipt, RBI Claim)
    ├── 7. Outbound WhatsApp Reply (Formatted message + optional Sarvam TTS voice)
    └── 8. Interactive Feedback Prompt (1 - Helpful, 2 - Not Helpful, 3 - Human, 4 - Wrong)
            │
            ▼ Live Polling Updates (Every 5-10s)
React Admin Dashboard & Metrics (:5173)
    ├── Live Escalations Queue with SLA Timers
    ├── 1-Click Human Supervisor Actions (Approve / Reject / Mark Fraud)
    └── Real-Time CSAT % and Telemetry Visuals
```

---

## 📋 Prerequisites

1. **Docker Desktop** installed and running.
2. **Dedicated Demo WhatsApp Number** on your phone (use a secondary SIM/number for hackathons).
3. **Sarvam AI API Key** (optional: if omitted, safe deterministic vernacular fallback is automatically used).
4. **PowerShell** (Windows) or **Bash** (macOS/Linux).

---

## 🚀 One-Command Launch (Step-by-Step)

### Step 1: Create Real Environment File
In your repository root:
```powershell
cd d:\hackathon\awaazledger
copy .env.real.example .env.real
```

Open `.env.real` in your text editor and update:
```env
# Set your actual sender phone number so the agent knows your profile
DEMO_WHATSAPP_NUMBER=+91XXXXXXXXXX

# If you have real Sarvam AI credentials:
ENABLE_SARVAM_REAL=true
SARVAM_API_KEY=your_actual_sarvam_key
SARVAM_STT_ENDPOINT=https://api.sarvam.ai/speech-to-text
SARVAM_TTS_ENDPOINT=https://api.sarvam.ai/text-to-speech
```
*(Note: If you do not have a live Sarvam API key right now, leave `ENABLE_SARVAM_REAL=false`. AwaazLedger will use its deterministic speech-to-text fallback so the demo never fails!)*

---

### Step 2: Spin Up Full Stack via Docker
Run the automated launcher:
```powershell
.\scripts\start_real_demo.ps1
```
*(Or on Linux/macOS: `./scripts/start_real_demo.sh`)*

Or run directly with Docker Compose:
```powershell
docker compose -f docker-compose.real.yml up --build -d
```

This launches:
- **Evolution API**: `http://localhost:8080`
- **AwaazLedger API**: `http://localhost:8000/docs`
- **Admin Dashboard**: `http://localhost:5173`

---

### Step 3: Link Your WhatsApp
Run the automated instance configuration script:
```powershell
python scripts/setup_evolution_instance.py
```

The script will:
1. Connect to Evolution API at `http://localhost:8080`.
2. Create the `paytm-awaazledger` instance and register the webhook pointing to `http://backend:8000/api/v1/webhooks/whatsapp`.
3. Save the pairing QR code to: `dist/evolution_qr.png`.
4. Render an ASCII QR code directly in your terminal.

**To scan from your phone:**
1. Open **WhatsApp** on your phone.
2. Go to **Settings** (or 3 dots on Android) -> **Linked Devices** -> **Link a Device**.
3. Scan the QR code displayed in the terminal or open `dist/evolution_qr.png`.
4. Once linked, Evolution API will show connected status.

---

### Step 4: Verify System Health
Run the diagnostic checklist script:
```powershell
python scripts/run_real_whatsapp_demo_checklist.py
```

---

## 📱 Live Demonstration Guide for Judges

### Test 1: Happy Path Voice Note (Instant Bridge Credit)
Send an audio voice note from your connected phone to the WhatsApp bot:
> *"Bhaiya maine 450 rupaye ka payment kiya, account se kat gaya lekin dukandar ko nahi mila. UTR 987654321012 hai."*

**What happens behind the scenes:**
1. Evolution API sends webhook to `/api/v1/webhooks/whatsapp`.
2. Sarvam AI transcribes vernacular Hindi and extracts `UTR: 987654321012`, `Amount: ₹450`.
3. 3-Way Reconciler checks SQLite mock database:
   - CBS = `DEBIT_SUCCESS`
   - NPCI = `U30 TIMEOUT`
   - Paytm = `PENDING`
4. Policy Engine verifies trust score (88/100) and executes **Instant ₹450 Bridge Credit**.
5. Outbound WhatsApp reply is sent back in < 15 seconds:
   ```text
   ✅ PROVISIONAL BRIDGE CREDIT PROVIDED

   Reference: DISP-XXXXXXXX
   Claimed Amount: ₹450.00

   INR 450.00 ka provisional bridge credit add kar diya gaya hai.
   Aap merchant ko ye reference dikha sakte hain.

   Financial Truth Trace:
   • Remitter Bank: ✅ Debited
   • NPCI Switch: ⏳ Delayed / In-Transit
   • Beneficiary Bank: ❌ Not Credited
   • Paytm Settlement: ⏳ Pending
   • Bridge Credit: ✅ Provided
   • RBI TAT Timer: ⏳ Active (T+1 Rule)
   ```
6. Agent follows up with the interactive feedback prompt:
   ```text
   Kripya apna feedback dein:
   1 - Helpful
   2 - Not helpful
   3 - Talk to human
   4 - Wrong decision
   ```

---

### Test 2: Feedback & Closed-Loop Learning
Reply on WhatsApp with:
```text
1
```
- The bot replies: *"Shukriya 🙏 Aapka feedback note kar liya gaya hai."*
- Switch to the browser at `http://localhost:5173/metrics`.
- Notice the **Customer Satisfaction %** card immediately updates to reflect the real rating.

Now try sending:
```text
3
```
- The bot replies: *"Aapka request supervisor desk ko bhej diya gaya hai. Kripya intezaar karein."*
- Switch to `http://localhost:5173/dashboard`.
- Notice a new open ticket appears on the **Supervisor Escalation Desk** with reason `CUSTOMER_REQUESTED_HUMAN_SUPPORT`!

---

### Test 3: Synthetic Fraud Defense
Send a text with a fabricated UTR:
> *"Mera ₹1,999 kat gaya. UTR 000000000000"*

- AwaazLedger flags invalid check-digits, zero CBS match, and low trust score.
- The bot responds with `🛡️ RISK VERIFICATION LOCK APPLIED`.
- The dispute is locked with zero monetary loss for Paytm.

---

### Test 4: High-Value Human Escalation
Send a high-ticket transaction:
> *"Payment stuck of ₹18,500 for flight ticket. UTR 998877665544"*

- AwaazLedger detects that ₹18,500 exceeds the autonomous ceiling (> ₹2,000).
- The bot replies that the case has been escalated to an Operations Specialist.
- Open `http://localhost:5173/dashboard`, inspect the evidence dossier, and click **Approve**!

---

## 🛠️ Troubleshooting Matrix

| Issue | Cause | Fix |
|---|---|---|
| **QR code expired or failed to link** | WhatsApp Web session timeout | Rerun `python scripts/setup_evolution_instance.py` and scan the fresh QR code. |
| **WhatsApp webhook not reaching backend** | Docker container network routing | Ensure `EVOLUTION_WEBHOOK_URL=http://backend:8000/api/v1/webhooks/whatsapp` in `.env.real`. |
| **"This number is not registered for demo"** | Sender phone not in map | Add your number to `data/phone_user_map.json` or set `DEMO_WHATSAPP_NUMBER=+91...` in `.env.real`. |
| **Sarvam STT returns timeout or 401** | Invalid key or network lag | The backend automatically falls back to `MOCK_SARVAM_FALLBACK` without failing the demo. |
| **Docker container exits** | Port conflict on 8000 or 8080 | Ensure no local uvicorn or local Evolution instance is running on those ports. |
