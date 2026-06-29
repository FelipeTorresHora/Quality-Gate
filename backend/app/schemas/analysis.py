from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import (
    AnalysisRunStatus,
    AnalysisTriggerSource,
    FindingCategory,
    FindingSeverity,
    GateDecision,
)

MockScenario = Literal[
    "passing",
    "coverage_fail",
    "security_fail",
    "technical_debt_fail",
    "mixed_fail",
]


class MockAnalysisRunCreate(BaseModel):
    scenario: MockScenario = "mixed_fail"
    pr_number: int = Field(default=1, ge=1)
    head_sha: str = "mock-head-sha"


class AnalysisFindingRead(BaseModel):
    id: UUID
    analysis_run_id: UUID
    category: FindingCategory
    severity: FindingSeverity
    file_path: str | None
    line_number: int | None
    title: str
    description: str
    blocking: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AnalysisRunSummary(BaseModel):
    id: UUID
    repository_id: UUID
    pr_number: int
    head_sha: str
    status: AnalysisRunStatus
    decision: GateDecision | None
    trigger_source: AnalysisTriggerSource
    score: float | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None
    finished_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class AnalysisRunDetail(AnalysisRunSummary):
    coverage_result_json: dict
    security_result_json: dict
    technical_debt_result_json: dict
    ai_review_json: dict
    pull_request_snapshot_json: dict
    changed_files_snapshot_json: list[dict]
    diff_truncated: bool
    final_report_markdown: str | None
    findings: list[AnalysisFindingRead]


class GitHubPublicationCommentResult(BaseModel):
    enabled: bool
    published: bool
    html_url: str | None = None
    skipped_reason: str | None = None


class GitHubPublicationStatusResult(BaseModel):
    enabled: bool
    published: bool
    target_sha: str | None = None
    state: str | None = None
    skipped_reason: str | None = None


class GitHubPublicationResult(BaseModel):
    analysis_run_id: UUID
    comment: GitHubPublicationCommentResult
    commit_status: GitHubPublicationStatusResult
