from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.analysis_run import AnalysisRun
from app.schemas.github import (
    GitHubPullRequestRead,
    PullRequestReviewRun,
    PullRequestReviewState,
)


def get_pull_request_review_state(
    db: Session, repository_id: UUID, pull_request: GitHubPullRequestRead
) -> PullRequestReviewState:
    latest_run = db.scalar(
        select(AnalysisRun)
        .where(
            AnalysisRun.repository_id == repository_id,
            AnalysisRun.pr_number == pull_request.number,
        )
        .order_by(AnalysisRun.created_at.desc(), AnalysisRun.id.desc())
        .limit(1)
    )
    if latest_run is None:
        return PullRequestReviewState(state="not_run", analysis_run=None)

    state = "current" if latest_run.head_sha == pull_request.head_sha else "outdated"
    return PullRequestReviewState(
        state=state,
        analysis_run=PullRequestReviewRun(
            id=latest_run.id,
            status=latest_run.status,
            decision=latest_run.decision,
            score=latest_run.score,
            trigger_source=latest_run.trigger_source,
            head_sha=latest_run.head_sha,
            created_at=latest_run.created_at,
        ),
    )
