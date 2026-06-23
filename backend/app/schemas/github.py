from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from app.models.enums import AnalysisRunStatus, AnalysisTriggerSource, GateDecision


class GitHubPullRequestRead(BaseModel):
    number: int
    title: str
    user_login: str
    state: str
    draft: bool
    head_ref: str
    head_sha: str
    base_ref: str
    html_url: str
    created_at: datetime
    updated_at: datetime


class PullRequestReviewRun(BaseModel):
    id: UUID
    status: AnalysisRunStatus
    decision: GateDecision | None
    score: float | None
    trigger_source: AnalysisTriggerSource
    head_sha: str
    created_at: datetime


class PullRequestReviewState(BaseModel):
    state: Literal["not_run", "current", "outdated"]
    analysis_run: PullRequestReviewRun | None


class GitHubPullRequestWithReviewState(GitHubPullRequestRead):
    review_state: PullRequestReviewState


class PullRequestSnapshot(BaseModel):
    number: int
    title: str
    body: str | None
    state: str
    draft: bool
    author_login: str
    html_url: str
    base_ref: str
    head_ref: str
    head_sha: str
    base_sha: str | None
    created_at: datetime
    updated_at: datetime


class ChangedFileSnapshot(BaseModel):
    filename: str
    status: str
    additions: int
    deletions: int
    changes: int
    patch: str | None = None


class PullRequestContextRead(BaseModel):
    pull_request: PullRequestSnapshot
    changed_files: list[ChangedFileSnapshot]
    diff_snapshot: str
    diff_truncated: bool


class GitHubWebhookResult(BaseModel):
    status: Literal["accepted"] = "accepted"
    ignored: bool
    reason: str | None = None
    analysis_run_id: UUID | None = None
