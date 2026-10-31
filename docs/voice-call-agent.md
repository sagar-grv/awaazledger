# AwaazLedger Voice Call AI Teammate
> *"Call instead of chat. Same autonomous dispute-resolution brain."*

---

## 1. Executive Summary & Why Voice Call Matters

While WhatsApp chat, voice notes, and screenshot OCR serve tech-savvy users well, millions of Indian users facing stuck UPI payments are:
- **Elderly or semi-literate users** who struggle with typing or navigating apps.
- **Shop counter buyers** in noisy, stressful checkout environments who need quick spoken assistance.
- **Vernacular speakers** who naturally communicate in Hindi, Marathi, or mixed Hinglish.

The **AwaazLedger Voice Call AI Teammate** allows a customer to simply **dial a number** (or launch a WebRTC browser call) and converse naturally with an AI teammate. The voice agent guides the user, extracts the 12-digit UTR, verifies the dispute across Bank CBS, NPCI switch, and Paytm ledgers, and speaks out the exact resolution.

---

## 2. Architectural Blueprint

```
                      ┌────────────────────────────────────────┐
                      │             CALLER CHANNEL             │
                      │  Phone PSTN / SIP  OR  WebRTC Browser  │
                      └──────────────────┬─────────────────────┘
                                         │
                   Audio Stream (RTP / WebSocket AudioSocket)
                                         ▼
                      ┌────────────────────────────────────────┐
                      │         TELEPHONY / AUDIO GATEWAY      │
                      │  FreeSWITCH / Asterisk / WebRTC Portal │
                      └──────────────────┬─────────────────────┘
                                         │
                               Audio Chunks / Base64
                                         ▼
                      ┌────────────────────────────────────────┐
                      │          Sarvam AI Saarika STT         │
                      │     (Real-time Vernacular Speech-to-Text)│
                      └──────────────────┬─────────────────────┘
                                         │
                             Transcribed Spoken Text
                                         ▼
                      ┌────────────────────────────────────────┐
                      │        CallDialogManager (State Machine)│
                      │   - Explicit Consent (RBI Recording)   │
                      │   - Dynamic Vernacular Language Adapt   │
                      │   - 12-Digit UTR Extraction (Speech/DTMF)│
                      │   - Missing UTR WhatsApp Link Fallback │
                      └──────────────────┬─────────────────────┘
                                         │
                             Verified Entities (UTR, Amount)
                                         ▼
      ┌──────────────────────────────────────────────────────────────────┐
      │               DETERMINISTIC DISPUTE ENGINE                      │
      │   (Zero Hallucination - Same Engine as WhatsApp Channel)         │
      │   ├─ 3-Way Financial Truth (CBS + NPCI UDIR + Paytm Ledger)     │
      │   ├─ RiskEngine (Trust Score, SwarmShield, Anomaly Flags)       │
      │   └─ PolicyEngine (₹2,000 Bridge Credit, Merchant Recovery)      │
      └──────────────────────────────────┬───────────────────────────────┘
                                         │
                            Resolution & Financial Action
                                         ▼
                      ┌────────────────────────────────────────┐
                      │          Sarvam AI Bulbul TTS          │
                      │     (Vernacular Text-to-Speech Output) │
                      └──────────────────┬─────────────────────┘
                                         │
                               Audio Response Stream
                                         ▼
                      ┌────────────────────────────────────────┐
                      │          CALLER HEARS RESOLUTION       │
                      │  • ₹450 Bridge Credit Credited          │
                      │  • Merchant Reference DISP-XXXXX       │
                      │  • End-of-Call DTMF/Spoken Feedback    │
                      └────────────────────────────────────────┘
```

---

## 3. Key Telephony & Safety Guardrails

| Guardrail | Implementation |
|---|---|
| **Zero Financial Hallucination** | The Voice AI agent does **not** move money. It only extracts transcribed entities and hands them off to the deterministic `RiskEngine` and `PolicyEngine`. |
| **Mandatory Consent** | Explicit call recording consent is required under RBI dispute guidelines before any financial information is collected. |
| **Multi-Modal DTMF Fallback** | Callers can speak their 12-digit UTR digit-by-digit ("nau aath saat...") or type it directly on their dialpad keypad. |
| **Missing UTR WhatsApp Bridge** | If a stressed user cannot find their UTR, the agent immediately sends a direct upload link to their WhatsApp number. |
| **Supervisor Telemetry Console** | Supervisors see live calls streaming in real time on the Operations Dashboard (`/dashboard`) with duration and live transcripts. |

---

## 4. Quick Testing & Demo Guide

### Option A: WebRTC Interactive Browser Call
1. Open the frontend: [http://localhost:5173/call](http://localhost:5173/call) or click **Voice Call Teammate** in the top navigation bar.
2. Select language (**हिंदी**, **मराठी**, or **English**).
3. Click **Call AI Teammate (Dial In)**.
4. Test any of the 4 Judges Scenarios with one click or speak into your microphone!

### Option B: Automated CLI Runner (All 7 Scenarios)
Run the automated test runner in PowerShell:
```powershell
python scripts/run_voice_call_demo.py
```
This executes all 7 scenarios offline with zero external dependencies:
1. Sharma Kirana Store (Instant Bridge Credit ₹450 - Hindi)
2. Reliance Fresh Soundbox Offline (Digital Merchant Receipt - Marathi)
3. High-Value Flight Booking (Escalated to Supervisor Desk - English)
4. Missing UTR Fallback (Automated WhatsApp Link Dispatched)
5. Spoken Hindi Number Words ("nau aath saat chhe...")
6. DTMF Keypad Mode (Keypad digits only)
7. Consent Refusal (Safe Termination under RBI Rule)

### Option C: Diagnostic Environment Check
```powershell
python scripts/setup_voice_call.py
```
Verifies backend connectivity, audio directories, and mock scenario files.
