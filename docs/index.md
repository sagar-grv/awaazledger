# AwaazLedger — Documentation Directory Index

Welcome to the comprehensive documentation library for **AwaazLedger**, an Autonomous AI Teammate for Self-Healing UPI Disputes developed for the **Paytm Build for India AI Hackathon (Track 3)**.

---

## Documentation Roadmap

| Document | Description | Target Audience |
|---|---|---|
| [**Architecture & Design**](architecture.md) | Technical architecture, system subsystems, data models, and API definitions. | Engineers & Judges |
| [**Architecture Diagrams**](architecture-diagrams.md) | Mermaid sequence diagrams, high-level architecture flows, and state machine transitions. | Architects & Reviewers |
| [**Decision Policy Engine**](decision-policy.md) | Deterministic decision rules, 5-factor risk scoring, RBI TAT thresholds, and action matrices. | Compliance & Risk Teams |
| [**Pitch Deck Content**](pitch-deck-content.md) | 7-slide presentation deck with speaker notes, visual guidelines, and competitive analysis. | Judges & Product Leads |
| [**Demo Video Script**](demo-video-script.md) | 2-minute timed scene-by-scene demo script with exact audio voiceovers and UI highlights. | Video Producers & Presenters |
| [**Judge Q&A Guide**](judge-qa.md) | 25+ detailed questions & answers covering financial risk, compliance, latency, and AI safety. | Hackathon Presenters |
| [**Submission Checklist**](submission-checklist.md) | Step-by-step readiness checklist covering code quality, scenarios, tests, and demo verification. | QA & Hackathon Team |
| [**Demo Execution Scripts**](demo-script.md) | CLI commands and guided walkthrough instructions for terminal and frontend demonstrations. | Developers & Evaluators |

---

## Quick Links to Key System Specs
- **Primary Execution API**: `POST /api/v1/agent/run/{dispute_id}`
- **Multimodal Ingestion API**: `POST /api/v1/ingest/text`, `POST /api/v1/ingest/voice`, `POST /api/v1/ingest/image`
- **Supervisor Operations Desk**: `GET /api/v1/escalations`, `POST /api/v1/escalations/{id}/action`
- **Real-Time Tracker API**: `GET /api/v1/disputes/{id}/tracker`
- **Swarm Shield Radar**: `GET /api/v1/swarm-shield`
- **Merchant Sale Recovery**: `POST /api/v1/disputes/{id}/merchant-recovery`
