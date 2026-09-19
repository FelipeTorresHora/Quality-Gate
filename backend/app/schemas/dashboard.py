from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import (
    AnalysisRunStatus,
    AnalysisTriggerSource,
    FindingCategory,
    FindingSeverity,
    GateDecision,
)

DashboardReviewState = Literal["current", "outdated", "not_run"]
DashboardOpenPullRequestActionKind = Literal[
    "fail",
    "error",
    "outdated",
    "publication_off",
]


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


class DashboardOpenPullRequestAction(BaseModel):
    repository_id: UUID
    repository_full_name: str
    pr_number: int
    pr_title: str | None
    html_url: str | None
    head_sha: str
    analysis_run_id: UUID
    status: AnalysisRunStatus
    decision: GateDecision | None
    review_state: DashboardReviewState
    action: DashboardOpenPullRequestActionKind
    comment_on_github: bool
    publish_github_status: bool
    created_at: datetime


class DashboardSummaryRead(BaseModel):
    total_repositories: int
    total_analysis_runs: int
    run_status_counts: dict[str, int]
    gate_decision_counts: dict[str, int]
    approval_rate: float | None
    recent_analysis_runs: list[DashboardRecentAnalysisRun]
    finding_counts: list[DashboardFindingCount]
    top_blocking_categories: list[DashboardBlockingCategory]
    open_pull_requests_needing_action: list[DashboardOpenPullRequestAction] = Field(
        default_factory=list
    )
