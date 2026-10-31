# AwaazLedger — Hackathon Submission Checklist

**Paytm Build for India AI Hackathon | Track 3: Autonomous AI Teammates**  
*Verification & Submission Readiness Protocol*

---

## 1. Hackathon Eligibility & Requirements
- [x] **Track Selected**: Track 3 — Autonomous AI Teammates
- [x] **Core Theme**: Autonomous resolution of pending/failed UPI disputes with zero hallucinations
- [x] **Zero Network Dependency for Demo**: All scenarios execute 100% reliably offline via deterministic seed data
- [x] **Pluggable Live Connectors**: Feature-flagged adapters for Sarvam AI STT, Tesseract OCR, and Evolution WhatsApp
- [x] **Human-in-the-Loop Collaboration**: Full Operations Supervisor Desk with one-click actions

---

## 2. Codebase & Test Verification
- [x] **Backend Unit Tests**: 102/102 tests passing (`python -m pytest tests -q`)
- [x] **Frontend TypeScript & Build**: Clean production build with Vite (`npm run build`)
- [x] **Database Migrations / Schema**: SQLite database auto-seeds all scenarios cleanly (`python scripts/seed_db.py`)
- [x] **Unified Demo Script**: Executes all 8 phases cleanly with zero errors (`python scripts/run_full_demo.py`)
- [x] **Swarm Shield Demo**: Demonstrates cluster outage detection (`python scripts/run_swarm_shield_demo.py`)
- [x] **Operations Demo**: Demonstrates supervisor SLA and one-click actions (`python scripts/run_ops_demo.py`)

---

## 3. Mandatory Demonstration Scenarios
- [x] **SCN-01: Happy Path Small-Ticket Grocery (₹450)**: Vernacular Hindi voice dispute → 3-Way Reconciliation → Instant ₹450 Bridge Credit.
- [x] **SCN-02: Delayed In-Transit Reversal (₹1,200)**: RBI TAT T+1 breach → Automatic ₹100/day penal compensation claim filed.
- [x] **SCN-03: High-Value Travel Ticket (₹18,500)**: Autonomous ceiling breach (> ₹2,000) → Escalated to Supervisor Desk with investigative dossier.
- [x] **SCN-04: Frequent Disputer Risk Flag (₹950)**: Low trust score (< 0.70) → Strict verification policy routing.
- [x] **SCN-05: Synthetic Fraud Containment (₹1,999)**: Fake UTR `000000000000` → Zero CBS match → Instant fraud containment block.
- [x] **EDGE-01: Ghost Success (₹780)**: Beneficiary credited on NPCI switch → Verified Digital Cashier Receipt issued.
- [x] **EDGE-02: Duplicate Debit (2x ₹1,500)**: Two CBS debits for single merchant order → Redundant debit auto-reversed.

---

## 4. UI / UX Features & Deliverables
- [x] **WhatsApp-Style Simulator**: Vernacular chat interface with audio player, quick scenario pills, and image upload.
- [x] **Real-Time Visual Multi-Node Tracker**: 4-node progression card with timer countdowns and live audit events.
- [x] **Supervisor Operations Desk**: Queue list, SLA urgency badges, full evidence dossiers, and one-click action buttons.
- [x] **Business Impact & Operations Dashboard**: Live metrics for autonomous resolution rate, bridge credit exposure, and RBI penalty savings.
- [x] **Swarm Shield Outage Banner**: Real-time switch alert banner with UPI Lite fallback suggestions.
- [x] **Merchant Recovery Drawer**: Instant QR code and collect link modal for safe checkout retry.

---

## 5. Submission Documentation & Pitch Pack
- [x] **Root README.md**: Complete project overview, architecture diagram, quickstart guide, and scenario matrix.
- [x] **docs/pitch-deck-content.md**: 7 presentation slides with complete speaker notes.
- [x] **docs/demo-video-script.md**: 2-minute timed scene-by-scene demo video walkthrough script.
- [x] **docs/judge-qa.md**: 25+ comprehensive technical, financial, and regulatory questions answered.
- [x] **docs/architecture-diagrams.md**: Mermaid diagrams for system architecture, state machine, and escalation flows.
- [x] **dist/awaazledger_pitch.pptx**: Auto-generated 7-slide PowerPoint presentation deck.
