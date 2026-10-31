# AwaazLedger Live Stage Demo Script (Paytm Build for India Track 3)

## Quick Pitch
> "Judges, every day millions of UPI users face a scary moment: their bank account is debited, but the merchant never receives the money. Traditional customer support takes 3 to 7 days, leaving small merchants and everyday consumers stranded.
> 
> Meet **AwaazLedger**: an autonomous AI teammate that ingests vernacular voice notes, screenshots, or messages on WhatsApp, performs instantaneous 3-way reconciliation against Core Banking, NPCI, and Paytm ledgers, and self-heals eligible disputes within seconds using instant Bridge Credit under RBI circular guidelines."

---

## 16-Step Live Stage Walkthrough

### Act 1: Instant Self-Healing with Bridge Credit (SCN-01)
1. **Select Demo Identity**: Choose **Rohit Verma** (`+919876543210`) from the top right selector.
2. **Trigger Scenario**: Click the **₹450 Pending UPI** button or type `"Mera 450 kat gaya Sharma Kirana pe UTR 987654321012"`.
3. **Show Ingestion**: The system registers the dispute and extracts UTR `987654321012` and Amount `₹450.00`.
4. **Agent Processing**: Watch the real-time checkpoints: Identity verified, CBS queried, NPCI UDIR queried, Paytm ledger checked.
5. **Outcome**: The AI teammate issues an **Instant Bridge Credit of ₹450.00**, starts the RBI 24h TAT timer, raises an NPCI auto-reversal ticket, and displays the **Live Multi-Node Tracker Card** showing Remitter Bank (SUCCESS), NPCI Switch (DELAYED U30), and Bridge Credit (SUCCESS).

---

### Act 2: Fraud Detection & Defense (SCN-05)
6. **Select Demo Identity**: Switch to **Vikram Singh** (`+919876543212`).
7. **Trigger Scenario**: Click **Fraud Invalid UTR** (`UTR 000000000000`).
8. **Outcome**: Risk score spikes to 85.0 (CRITICAL). The Policy Engine triggers **Rule 1 (Fraud Control Block)**. No bridge credit is issued; the account is locked from automated disbursements and routed to the fraud queue with a `Fraud Control Lock` badge.

---

### Act 3: High-Value Human-in-the-Loop Escalation (SCN-03)
9. **Select Demo Identity**: Switch to **Priya Sharma** (`+919876543211`).
10. **Trigger Scenario**: Click **₹18,500 High Value** (Flight ticket payment stuck).
11. **Outcome**: The reconciliation verifies the debit, but the amount exceeds the autonomous safety ceiling of ₹2,000. The agent triggers **Rule 4 (Human Escalation)**, creates an L2 operations ticket with a 15-minute SLA, and clearly informs Priya in English.

---

### Act 4: Ghost-Success Receipt Generation (EDGE-01)
12. **Select Demo Identity**: Switch to **Sunita Devi** (`+919876543214`).
13. **Trigger Scenario**: Click **Ghost Success ₹780** (Reliance Fresh).
14. **Outcome**: The 3-way reconciliation uncovers that the beneficiary merchant **was already credited** on the switch. The AI teammate triggers **Rule 2**, suppresses bridge credit, and generates a digitally signed **Verified Merchant Receipt** for Sunita to show the cashier.

---

### Act 5: Duplicate Debit & Amount Mismatch Safety
15. **Select Demo Identity**: Switch to **Amit Kumar** (`+919876543213`).
16. **Trigger Scenario**: Click **Duplicate Debit ₹650**. The system detects 2 debit legs within the 120-second duplicate window and escalates to a human supervisor to prevent double refunding.

---

### Act 6: Human Supervisor Operations Desk (Live Human-in-the-Loop)
17. **Navigate to Supervisor Desk**: Click **Operations Desk** in top navigation.
18. **Review Prioritized Queue**: Notice how the ₹18,500 flight ticket dispute (`DISP-SCN-03`) and the invalid UTR claim are queued at the top with SLA countdown indicators.
19. **Open Investigative Dossier**: Click **Dossier** on Ticket #1 to inspect the customer's KYC trust score, transaction facts, and the deterministic 3-way reconciliation matrix (CBS, NPCI, Paytm).
20. **Execute 1-Click Approval**: Click **1-Click Approve & Disburse Bridge Credit**. Watch the ticket transition to `APPROVED`, an immutable audit record get minted, and instant bridge credit disbursed to Priya Sharma.

---

### Act 7: Real-Time Fintech Telemetry & Impact Analytics
21. **Navigate to Metrics Dashboard**: Click **Metrics** in the top navigation.
22. **Present Live Telemetry to Judges**:
   - **Autonomous Resolution Rate**: 50.0% of disputes self-healed end-to-end with zero human touch.
   - **Total Bridge Credits Disbursed**: Real live DB sum showing ₹19,420.00 liquidity protected.
   - **RBI Non-Compliance Penalty Avoidance**: Live tally of compensation claims filed under RBI circular guidelines.
   - **Operational Velocity**: Sub-second agent resolution replacing the 72-hour legacy turnaround.
   - **Projected Impact**: Annualized L1 cost savings and 71.8 hours TAT reduction per dispute.

---

## Technical Architecture Highlights for Judges
- **Deterministic Separation**: Financial fact verification is 100% deterministic (no LLM hallucination in money movement).
- **RBI Circular Compliance**: Automatic ₹100/day delay compensation claim filing when transactions exceed the T+1 statutory TAT.
- **Multimodal Flexibility**: Handles vernacular Hindi/Marathi voice notes (Sarvam AI STT) and payment receipt screenshots (OCR).
- **Pluggable Integration**: Seamlessly switches between the React simulator and production WhatsApp gateways (Evolution API / Meta Cloud API).
