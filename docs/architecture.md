# AwaazLedger System Architecture

AwaazLedger is engineered as a **5-Tier Autonomous Agent Platform** designed specifically for Indian digital payments and RBI compliance.

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Multimodal Channel Ingestion Layer                       │
│    WhatsApp (Evolution API / Meta Cloud) | React Simulator  │
│    Voice Note Ingest (Sarvam AI STT) | Screenshot OCR       │
│    Channel Identity Service (E.164 Phone-to-User Mapping)   │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│ 2. Intent & Entity Extraction Layer                         │
│    Deterministic Regex & NLP Parser (Hindi, Marathi, Hinglish)│
│    UTR, Amount, Merchant, and Intent Classifier             │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│ 3. 3-Way Reconciliation & Financial Truth Layer             │
│    Bank Core Banking System (CBS) Adapter                   │
│    NPCI UDIR Switch Adapter                                 │
│    Paytm Payment Gateway Ledger                             │
│    Customer Trust & Reputation Engine                       │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│ 4. Deterministic Risk & Policy Governance Engine            │
│    RBI Circular TAT Calculator (INR 100/day penalty)        │
│    Instant Bridge Credit Safeguard (Ceiling: INR 2,000)     │
│    Fraud Velocity Scoring & Sanity Checkers                 │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│ 5. Self-Healing Action & Compliance Dispatcher              │
│    Disburse Instant Bridge Credit                           │
│    File NPCI Auto-Reversal Ticket                           │
│    Submit RBI Delay Compensation Claim                      │
│    Issue Digitally Signed Verified Merchant Receipt         │
│    Human Escalation Operations Dashboard                    │
│    Tamper-Evident Audit Trail & Bilingual Explanations      │
└─────────────────────────────────────────────────────────────┘
```

## Tier 1 & 2: Multimodal Channel Ingestion & Intent Extraction

1. **Pluggable Channel Adapters**:
   - `SimulatorAdapter`: Built-in web simulator for 100% reliable hackathon presentation.
   - `EvolutionWhatsAppAdapter`: Baileys/Evolution API open-source WhatsApp gateway with payload normalization.
   - `MetaCloudWhatsAppAdapter`: Placeholder adapter for enterprise Meta WhatsApp Cloud API.
2. **Channel Identity Resolution**:
   - Canonical E.164 phone number mapping via `data/phone_user_map.json`.
   - Automatic user KYC and trust profile retrieval.
3. **Multilingual Intent & Entity Extraction**:
   - Deterministic extraction supporting Devanagari Hindi, Marathi, and Hinglish.
   - Robust currency extraction matching `₹450`, `Rs 450`, `INR 18,500`, `450 रुपये`, `450 rupaye`.
   - Standalone 12-to-20 digit UTR extraction prioritizing 12-digit UPI sequences.

## Tier 3: The Financial Truth Layer (Deterministic Verification)

The Three-Way Reconciliation Engine operates under the **separation of facts and decisions**:
1. **Facts, Not Decisions**: The reconciliation service queries CBS, NPCI UDIR, Paytm ledger, and User Trust. It evaluates technical facts (e.g., whether debit succeeded, whether beneficiary was credited, whether duplicate debits occurred) and produces verifiable `policy_inputs`.
2. **Deterministic Mock Simulation**: External banking systems (Core Banking Systems, NPCI UDIR switch, and Paytm internal ledger) are deterministically simulated using seeded database state to ensure 100% testable and reproducible dispute resolution.

## Tier 4 & 5: Autonomous Policy & Action Dispatcher

1. **Risk Scoring Engine**: Deterministic multi-factor scoring of fraud risk (`0.0` to `100.0`) and operational risk level (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).
2. **Prioritized Governance Rules**:
   - Rule 1: Fraud Control Lock (Invalid UTR, blacklisted user, severe amount mismatch).
   - Rule 2: Ghost-Success Receipt Generation (Merchant credited on NPCI/Paytm ledger).
   - Rule 3: Missing/Ambiguous Info Request (Prompts user for 12-digit UTR).
   - Rule 4: Human-in-the-Loop Operations Escalation (> ₹2,000 ceiling, duplicate debits).
   - Rule 5: Auto-Resolve with Instant Bridge Credit (Verified bank debit, high trust, within ₹2,000 ceiling).
   - Rule 6: Fallback Safe Escalation.

## Tier 6: Human Supervisor Operations Desk & Fintech Telemetry

1. **Prioritized Escalation Desk**:
   - Tickets auto-prioritized by risk severity: `CRITICAL` (1), `HIGH` (2), `MEDIUM` (3), `LOW` (4), and sorted by SLA deadline.
   - Real-time SLA countdown and breach detection against RBI T+1 turnaround deadlines.
2. **One-Click Audited Interventions**:
   - `Approve & Bridge Credit`: Idempotent disbursement of instant bridge credit with audit logging and dispute status transition to `RESOLVED`.
   - `Request Customer Info`: Flags ticket to `INFO_REQUESTED` and sends bilingual inquiry back to customer channel.
   - `Confirm Fraud & Block`: Blocks dispute to `FRAUD_BLOCKED` and issues internal security alert.
   - `Assign Ticket`: Reassigns ticket to specialized L2/Fraud investigators and updates status to `IN_REVIEW`.
3. **Investigative Financial Truth Dossier**:
   - Full 3-way banking breakdown (CBS debit confirmation, NPCI switch transit hold, Paytm settlement status).
   - Customer KYC and trust scoring profile.
   - End-to-end cryptographic audit trail recording every agent and human action.
4. **Real-Time Telemetry & Impact Projections**:
   - Live database aggregation of total disputes, autonomous resolution rate (%), bridge credit exposure (INR), and RBI compensation claims.
   - Transparent impact projections calibrated against industry benchmarks (`data/impact_benchmarks.json`):
     - INR 30 / ticket L1 manual handling cost savings
     - 71.8 hours TAT reduction (from 72 hours down to 12.4 minutes)
     - INR 100 / day RBI non-compliance penalty avoidance.

