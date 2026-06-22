from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.models.enums import (
    AnalysisRunStatus,
    AnalysisTriggerSource,
    FindingCategory,
    FindingSeverity,
    GateDecision,
)


class DashboardRecentAnalysisRun(BaseModel):
    id: UUID
    repository_id: UUID
    repository_full_name: str
    pr_number: int
    head_sha: str
    status: AnalysisRunStatus
    decision: GateDecision | None
    trigger_source: AnalysisTriggerSource
    score: float | None
    created_at: datetime


class DashboardFindingCount(BaseModel):
    category: FindingCategory
    severity: FindingSeverity
    count: int


class DashboardBlockingCategory(BaseModel):
    category: FindingCategory
    count: int


class DashboardSummaryRead(BaseModel):
    total_repositories: int
    total_analysis_runs: int
    run_status_counts: dict[str, int]
    gate_decision_counts: dict[str, int]
    approval_rate: float | None
    recent_analysis_runs: list[DashboardRecentAnalysisRun]
    finding_counts: list[DashboardFindingCount]
    top_blocking_categories: list[DashboardBlockingCategory]
