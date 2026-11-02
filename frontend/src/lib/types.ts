export type DisputeStatus =
  | 'PENDING'
  | 'ANALYZING'
  | 'AUTO_CREDITED'
  | 'ESCALATED'
  | 'RESOLVED'
  | 'REJECTED'
  | 'FRAUD_BLOCKED'
  | 'RECEIPT_GENERATED'
  | 'INFO_REQUESTED'
  | 'CLOSED';

export type AgentDecision =
  | 'AUTO_RESOLVE'
  | 'AUTO_RESOLVE_CREDIT'
  | 'AUTO_CREDIT'
  | 'GHOST_SUCCESS_RECEIPT'
  | 'HUMAN_ESCALATE'
  | 'FRAUD_BLOCK'
  | 'INFO_REQUEST'
  | 'REQUEST_INFO'
  | 'PENDING_ANALYSIS'
  | 'MANUALLY_APPROVED'
  | 'MANUALLY_REJECTED'
  | 'MANUALLY_BLOCKED_FRAUD';

export interface DemoUser {
  user_id: number;
  name: string;
  phone: string;
  paytm_id: string;
  language: string;
}

export interface ExtractedEntity {
  utr?: string;
  amount?: number;
  currency?: string;
  bank?: string;
  merchant_name?: string;
  timestamp?: string;
  language?: string;
  intent?: string;
  confidence?: number;
  missing_fields?: string[];
  raw_text?: string;
}

export interface IngestResponse {
  channel: string;
  user_id?: number;
  dispute_id?: number;
  dispute_code?: string;
  needs_more_info: boolean;
  agent_message: string;
  entities: ExtractedEntity;
  transcript?: string;
  ocr_json?: Record<string, any>;
}

export interface AgentAction {
  action_type: string;
  status: string;
  payload: Record<string, any>;
}

export interface TrackerNode {
  label: string;
  status:
    | 'SUCCESS'
    | 'PENDING'
    | 'FAILED'
    | 'DELAYED'
    | 'NOT_APPLICABLE'
    | 'ACTIVE'
    | 'CLAIM_FILED'
    | 'NOT_STARTED'
    | string;
  detail?: string;
}

export interface TrackerResponse {
  dispute_id: number;
  dispute_code: string;
  utr?: string;
  amount?: number;
  status: string;
  decision?: string;
  risk_level?: string;
  nodes: TrackerNode[];
  actions: AgentAction[];
  explanation_user?: string;
  explanation_internal?: string;
  state_history?: Array<Record<string, any>>;
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'agent' | 'system';
  text: string;
  timestamp: string;
  badge?: string;
  isAudio?: boolean;
  isImage?: boolean;
  imageUrl?: string;
  audioUrl?: string;
  disputeCode?: string;
  disputeId?: number;
  tracker?: TrackerResponse;
  processingSteps?: string[];
}

export interface Dispute {
  id: number;
  dispute_code: string;
  user_id: number;
  transaction_id?: number;
  channel: string;
  description?: string;
  amount: number;
  status: DisputeStatus;
  agent_decision: AgentDecision;
  confidence_score: number;
  created_at: string;
}

export interface Escalation {
  id: number;
  dispute_id: number;
  dispute_code?: string;
  user_name?: string;
  user_phone?: string;
  amount?: number;
  priority: string;
  reason: string;
  assigned_to?: string;
  sla_deadline?: string;
  status: string;
  resolution_note?: string;
  resolution_notes?: string;
  created_at: string;
  resolved_at?: string;
  updated_at?: string;
  is_sla_breached?: boolean;
  hours_to_sla?: number;
}

export interface EscalationListResponse {
  items: Escalation[];
  total: number;
  open_count: number;
  sla_breached_count: number;
}

export interface EscalationDetail {
  escalation: Escalation;
  dispute: Record<string, any>;
  user: Record<string, any>;
  transaction?: Record<string, any>;
  three_way_reconciliation?: Record<string, any>;
  risk_assessment?: Record<string, any>;
  policy_evaluation?: Record<string, any>;
  actions_taken: Array<Record<string, any>>;
  audit_trail: Array<Record<string, any>>;
  evidence_items: Array<Record<string, any>>;
}

export interface SupervisorActionRequest {
  note?: string;
  supervisor_id?: string;
  action_reason?: string;
  requested_info_prompt?: string;
}

export interface SupervisorActionResponse {
  escalation_id: number;
  dispute_id: number;
  action: string;
  status: string;
  message: string;
  bridge_credit_id?: number;
  timestamp: string;
}

export interface MetricBucket {
  key: string;
  count: number;
  percentage: number;
}

export interface MetricsSummary {
  total_disputes: number;
  processed_disputes?: number;
  auto_resolved_count: number;
  auto_resolution_rate_pct: number;
  auto_credited_count?: number;
  receipt_generated_count?: number;
  escalated_count: number;
  open_escalations_count?: number;
  fraud_blocked_count?: number;
  info_requested_count?: number;
  rejected_count?: number;
  bridge_credits_disbursed_inr: number;
  avg_resolution_seconds: number;
  rbi_claims_filed_count?: number;
  rbi_claims_saved_inr: number;
  feedback_count?: number;
  helpful_count?: number;
  not_helpful_count?: number;
  human_request_count?: number;
  wrong_decision_count?: number;
  customer_satisfaction_pct?: number;
  pending_feedback_count?: number;
  projected_annual_l1_cost_savings_inr?: number;
  projected_tat_reduction_hours?: number;
  estimated_rbi_penalties_prevented_inr?: number;
  benchmarks_version?: string;
}

export interface MetricsDistribution {
  by_bank: MetricBucket[];
  by_outcome: MetricBucket[];
  by_risk_level: MetricBucket[];
  by_decision: MetricBucket[];
  by_priority: MetricBucket[];
}

export interface OperationsHealth {
  system_status: string;
  open_escalations: number;
  sla_breached_escalations: number;
  oldest_pending_hours: number;
  avg_supervisor_resolution_minutes: number;
  auto_resolution_rate_pct: number;
  active_bridge_credit_exposure_inr: number;
}

export interface MetricsDashboard {
  summary: MetricsSummary;
  distributions: MetricsDistribution;
  operations_health: OperationsHealth;
}
