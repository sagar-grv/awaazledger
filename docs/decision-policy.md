# Deterministic Decision Policy Specification

AwaazLedger enforces strict regulatory compliance by decoupling **financial fact verification** from **policy decisions**.

---

## 1. Separation of Concerns: Financial Facts vs. Policy Decisions

1. **Reconciliation Engine (Financial Truth Layer)**:
   - Queries Bank Core Banking Systems (CBS), NPCI UDIR switch, and Paytm internal ledger.
   - Computes deterministic facts: `cbs_debited`, `beneficiary_credited`, `invalid_utr`, `user_mismatch`, `duplicate_debit`, `ghost_success`, and `amount_mismatch`.
   - Compiles these facts into structured `policy_inputs`.
   - **Does NOT decide whether to credit or block funds directly.**

2. **Policy Engine (Downstream Governance)**:
   - Ingests `policy_inputs` from the reconciliation report.
   - Evaluates regulatory rules (RBI Circular DPSS.CO.PD No.629/02.01.014/2019-20), user trust bands, and risk ceilings.
   - Maps inputs to one of the four decision states.

---

## 2. Seeded Scenarios and Signal Mapping

| Scenario | UTR | Expected Signal | Core Facts | Policy Impact |
|---|---|---|---|---|
| **SCN-01** | `987654321012` | `AUTO_ELIGIBLE` | CBS debited, NPCI U30, Beneficiary not credited, Trust 95 | Eligible for Instant Bridge Credit |
| **SCN-02** | `112233445566` | `AUTO_ELIGIBLE` | CBS debited, Timeout at beneficiary, Amount INR 120 | Eligible for Instant Bridge Credit |
| **SCN-03** | `998877665544` | `HUMAN_REVIEW` | CBS debited, NPCI U30, Amount INR 18,500 > INR 2,000 | Requires human supervisor approval |
| **SCN-04** | `445566778899` | `RBI_COMPENSATION_SIGNAL` | Pending > T+1 days (3 days delay) | Eligible for INR 200 delay compensation |
| **SCN-05** | `000000000000` | `FRAUD_SIGNAL` | UTR not found on switch, User trust 25 (Blacklisted) | Block credit, route to Anti-Fraud unit |
| **Ghost Success** | `556677889900` | `RECEIPT_ONLY` | Beneficiary credited, Settlement settled | Issue verified receipt; deny refund |
| **Duplicate Debit** | `778899001123` | `HUMAN_REVIEW` | 2 identical debits within 20 seconds | Route to human operations review |
| **Amount Mismatch** | `334455667788` | `FRAUD_OR_REVIEW` | User claims INR 5,000, Bank debited INR 500 | Flag severe discrepancy |

---

## 3. Four Core Decision States

### 1. `AUTO_RESOLVE`
- **Criteria**:
  - `policy_inputs.eligible_for_automatic_bridge_credit_signal == True`
  - CBS confirmed debited: `True`
  - Beneficiary credited: `False` / `Timed Out`
  - Transaction amount <= `AUTO_CREDIT_CEILING` (Default: INR 2,000)
  - User Trust Score >= `MIN_TRUST_SCORE` (Default: 85)
  - Fraud Velocity Score <= `MAX_FRAUD_SCORE` (Default: 30)
- **Triggered Actions**:
  - Disburse Instant Bridge Credit
  - Raise NPCI UDIR Auto-Reversal Ticket
  - Send empathetic vernacular customer notification

### 2. `HUMAN_ESCALATE`
- **Criteria**:
  - `policy_inputs.requires_human_review_signal == True`
  - Amount > `AUTO_CREDIT_CEILING`
  - OR Duplicate debit pattern detected
  - OR Minor amount mismatch (<= INR 100)
  - OR User Trust Score between 50 and 84
- **Triggered Actions**:
  - Package 3-way logs and OCR evidence into Human Escalation Dashboard
  - Notify customer of priority SLA review window (2 hours)

### 3. `FRAUD_BLOCK`
- **Criteria**:
  - `policy_inputs.fraud_block_signal == True`
  - User Trust Score < 50 OR User flagged in risk blacklist
  - Invalid UTR (not found in CBS/NPCI)
  - Identity mismatch (dispute user != transaction owner)
  - Severe amount mismatch (> INR 100 and > 10%)
- **Triggered Actions**:
  - Deny automated credit
  - Log audit anomaly
  - Route to Anti-Fraud / AML team

### 4. `INFO_REQUEST`
- **Criteria**:
  - UTR unextractable from voice/screenshot or missing
  - Multiple matching transactions found in same time window
- **Triggered Actions**:
  - Ask user for clarification via channel with interactive suggestions

---

## 4. Supervisor Human-in-the-Loop Actions & State Transitions

When an edge case or high-value transaction routes to `HUMAN_ESCALATE`, the human supervisor operations desk provides four idempotent, fully audited actions:

1. **`APPROVE` (One-Click Manual Bridge Credit)**:
   - **Preconditions**: Ticket status is `OPEN` or `IN_REVIEW`.
   - **Database Effects**:
     - `Escalation.status = "APPROVED"`, `resolved_at = now()`.
     - `Dispute.status = "RESOLVED"`, `agent_decision = "MANUALLY_APPROVED"`.
     - `BridgeCredit` issued under idempotency key `manual-bridge:{dispute_code}`.
     - `Action(BRIDGE_CREDIT_ISSUED)` and `AuditLog(ESCALATION_APPROVED)` recorded.
2. **`REJECT` (Manual Rejection)**:
   - **Preconditions**: Ticket status is `OPEN` or `IN_REVIEW`.
   - **Database Effects**:
     - `Escalation.status = "REJECTED"`, `Dispute.status = "REJECTED"`.
     - `Action(NOTIFY_USER)` and `AuditLog(ESCALATION_REJECTED)` recorded.
3. **`REQUEST_INFO` (Customer Prompt)**:
   - **Preconditions**: Ticket status is `OPEN` or `IN_REVIEW`.
   - **Database Effects**:
     - `Escalation.status = "INFO_REQUESTED"`, `Dispute.status = "INFO_REQUESTED"`.
     - User-facing prompt dispatched to WhatsApp simulator.
4. **`MARK_FRAUD` (Fraud Lock)**:
   - **Preconditions**: Confirmed suspicious activity or synthetic UTR.
   - **Database Effects**:
     - `Escalation.status = "FRAUD_CONFIRMED"`, `Dispute.status = "FRAUD_BLOCKED"`.
     - Account locked; `AuditLog(ESCALATION_FRAUD_MARKED)` recorded.
5. **`ASSIGN` (Supervisor Assignment)**:
   - **Preconditions**: Unassigned or reassigned ticket.
   - **Database Effects**:
     - `Escalation.assigned_to = assignee`, status advances to `IN_REVIEW`.

