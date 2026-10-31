# AwaazLedger — Architecture Diagrams

This document contains Mermaid diagrams illustrating the architectural components, data flows, and state machines of AwaazLedger.

---

## 1. High-Level System Architecture

```mermaid
flowchart TD
    subgraph Ingestion["1. Multimodal Channel Ingestion"]
        UI["WhatsApp Simulator / React UI"]
        WA["WhatsApp via Evolution API"]
        Audio["Voice Note (Hindi / Regional)"]
        OCR["Payment Screenshot"]
        
        UI -->|Text / Voice / Image| ChannelRouter["Channel Message Router"]
        WA -->|Webhook Payload| ChannelRouter
        Audio -->|Speech Audio| Sarvam["Sarvam AI STT Engine / Fallback"]
        OCR -->|Image Bytes| Vision["Tesseract OCR / Fallback"]
        Sarvam --> Intent["Intent & Entity Extractor"]
        Vision --> Intent
        ChannelRouter --> Intent
    end

    subgraph Truth["2. Financial Truth Layer"]
        CBS["Mock Core Banking System (CBS)"]
        NPCI["Mock NPCI UDIR Switch"]
        Ledger["Mock Paytm Settlement Ledger"]
        Recon["3-Way Reconciliation Service"]
        
        Recon -->|Verify Debit Status| CBS
        Recon -->|Verify Switch Transit & Reason Code| NPCI
        Recon -->|Verify Beneficiary Credit| Ledger
    end

    subgraph Brain["3. Autonomous Agent Brain"]
        Orch["Agent Orchestrator (State Machine)"]
        Risk["Composite Risk Engine (5 Factors)"]
        Policy["Deterministic Policy Engine"]
        Trust["User Trust Scoring Service"]
        
        Intent -->|Dispute Ticket| Orch
        Orch --> Recon
        Orch --> Trust
        Trust --> Risk
        Recon --> Risk
        Risk --> Policy
    end

    subgraph Actions["4. Action Dispatcher & Operations"]
        Dispatch["Action Dispatcher"]
        Bridge["Instant Bridge Credit (<= Rs 2,000)"]
        Receipt["Ghost-Success Digital Cashier Receipt"]
        RBI["RBI Penal Claim Filing (Rs 100/day)"]
        FraudBlock["Fraud Containment & Limit Lock"]
        EscDesk["Supervisor Escalation Desk (Human-in-the-Loop)"]
        
        Policy -->|AUTO_RESOLVE| Dispatch
        Policy -->|GHOST_SUCCESS| Dispatch
        Policy -->|FRAUD_BLOCK| Dispatch
        Policy -->|ESCALATE_HUMAN| EscDesk
        
        Dispatch --> Bridge
        Dispatch --> Receipt
        Dispatch --> RBI
        Dispatch --> FraudBlock
    end

    subgraph Radar["5. Swarm Shield & Recovery Radar"]
        Swarm["Swarm Shield Switch Outage Radar"]
        Recovery["Merchant Sale Recovery Link Generator"]
        
        NPCI -.->|Timeout Cluster U30/U69| Swarm
        Bridge -.->|Safe Checkout Retry| Recovery
    end

    subgraph Audit["6. Immutable Audit Trail"]
        DB[("SQLite / PostgreSQL Ledgers")]
        AuditLog["Audit Service (Microsecond Logs)"]
        
        Dispatch --> AuditLog
        EscDesk --> AuditLog
        AuditLog --> DB
    end
```

---

## 2. Autonomous Agent State Machine

```mermaid
stateDiagram-v2
    [*] --> INGESTION: User sends text / voice / screenshot
    INGESTION --> ENTITY_EXTRACTION: Ingest message payload
    ENTITY_EXTRACTION --> RECONCILIATION: Extracted UTR & claimed amount
    ENTITY_EXTRACTION --> NEEDS_INFO: Missing UTR / Ambiguous details
    NEEDS_INFO --> INGESTION: User provides missing info

    RECONCILIATION --> RISK_EVALUATION: 3-Way Reconciled (CBS + NPCI + Paytm)
    RISK_EVALUATION --> POLICY_DECISION: Composite Risk Score (0-100)

    POLICY_DECISION --> AUTO_RESOLVE: Low Risk + Valid Debit + Amount <= Rs 2,000
    POLICY_DECISION --> GHOST_SUCCESS: Switch shows Beneficiary Credited
    POLICY_DECISION --> FRAUD_BLOCK: Synthetic UTR / No CBS Debit / Blacklisted
    POLICY_DECISION --> ESCALATE_HUMAN: High Value (> Rs 2,000) / Duplicate Debit

    AUTO_RESOLVE --> BRIDGE_CREDITED: ActionDispatcher issues credit
    GHOST_SUCCESS --> RECEIPT_ISSUED: Digital Cashier Receipt generated
    FRAUD_BLOCK --> CONTAINED: Fraud lock applied & logged

    ESCALATE_HUMAN --> SUPERVISOR_QUEUE: Routed to Operations Desk
    SUPERVISOR_QUEUE --> APPROVED: Supervisor manual approval
    SUPERVISOR_QUEUE --> REJECTED: Supervisor manual rejection
    SUPERVISOR_QUEUE --> FRAUD_FLAGGED: Supervisor confirms fraud

    BRIDGE_CREDITED --> [*]
    RECEIPT_ISSUED --> [*]
    CONTAINED --> [*]
    APPROVED --> [*]
    REJECTED --> [*]
    FRAUD_FLAGGED --> [*]
```

---

## 3. End-to-End Sequence Flow

```mermaid
sequenceDiagram
    autonumber
    actor Customer as User (Rohit Sharma)
    participant Channel as WhatsApp Simulator
    participant Agent as Autonomous Agent Brain
    participant Truth as 3-Way Reconciliation
    participant Dispatch as Action Dispatcher
    participant DB as System Ledger & Audit

    Customer->>Channel: Sends Hindi Voice Note (Rs 450)
    Channel->>Agent: Ingest audio & extract entities
    Note over Agent: UTR: 987654321012, Amount: Rs 450
    Agent->>Truth: Execute 3-Way Reconciliation
    Truth-->>Agent: CBS: DEBIT_SUCCESS | NPCI: U30 TIMEOUT | Paytm: PENDING
    Note over Agent: Risk Engine: Trust=0.88, Risk=LOW (12/100)
    Note over Agent: Policy: AUTO_RESOLVE (Bridge Credit Eligible)
    Agent->>Dispatch: Execute Bridge Credit (Rs 450)
    Dispatch->>DB: Credit Rs 450 to User Wallet
    Dispatch->>DB: Record Action & Immutable Audit Log
    Agent-->>Channel: Return explainable Hindi message & Live Tracker
    Channel-->>Customer: "Aapke Paytm wallet me Rs 450 provisional credit bhej diya gaya hai!"
```
