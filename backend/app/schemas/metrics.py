"""Fintech operational metrics, SLA tracking, feedback satisfaction, and impact schemas."""

from typing import List, Optional
from pydantic import BaseModel, Field


class MetricBucket(BaseModel):
    key: str
    count: int
    percentage: float


class MetricsSummaryResponse(BaseModel):
    # Real DB Counts
    total_disputes: int
    processed_disputes: int = 0
    auto_resolved_count: int
    auto_resolution_rate_pct: float
    auto_credited_count: int = 0
    receipt_generated_count: int = 0
    escalated_count: int
    open_escalations_count: int = 0
    fraud_blocked_count: int = 0
    info_requested_count: int = 0
    rejected_count: int = 0
    bridge_credits_disbursed_inr: float
    avg_resolution_seconds: float
    rbi_claims_filed_count: int = 0
    rbi_claims_saved_inr: float

    # Customer Feedback & CSAT Metrics
    feedback_count: int = 0
    helpful_count: int = 0
    not_helpful_count: int = 0
    human_request_count: int = 0
    wrong_decision_count: int = 0
    customer_satisfaction_pct: float = 100.0
    pending_feedback_count: int = 0

    # Impact Projections (Explicitly labeled)
    projected_annual_l1_cost_savings_inr: float = 0.0
    projected_tat_reduction_hours: float = 0.0
    estimated_rbi_penalties_prevented_inr: float = 0.0
    benchmarks_version: str = "v1.0"


class MetricsDistributionResponse(BaseModel):
    by_bank: List[MetricBucket] = Field(default_factory=list)
    by_outcome: List[MetricBucket] = Field(default_factory=list)
    by_risk_level: List[MetricBucket] = Field(default_factory=list)
    by_decision: List[MetricBucket] = Field(default_factory=list)
    by_priority: List[MetricBucket] = Field(default_factory=list)


class OperationsHealthResponse(BaseModel):
    system_status: str = "HEALTHY"  # HEALTHY, ATTENTION_REQUIRED, DEGRADED
    open_escalations: int = 0
    sla_breached_escalations: int = 0
    oldest_pending_hours: float = 0.0
    avg_supervisor_resolution_minutes: float = 0.0
    auto_resolution_rate_pct: float = 0.0
    active_bridge_credit_exposure_inr: float = 0.0


class MetricsDashboardResponse(BaseModel):
    summary: MetricsSummaryResponse
    distributions: MetricsDistributionResponse
    operations_health: OperationsHealthResponse
