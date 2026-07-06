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
    return get_pull_request_review_states(
        db, repository_id, [pull_request]
    )[pull_request.number]


def get_pull_request_review_states(
    db: Session, repository_id: UUID, pull_requests: list[GitHubPullRequestRead]
) -> dict[int, PullRequestReviewState]:
    pr_numbers = [pull_request.number for pull_request in pull_requests]
    if not pr_numbers:
        return {}

    latest_runs_by_pr_number: dict[int, AnalysisRun] = {}
    runs = db.scalars(
        select(AnalysisRun)
        .where(
            AnalysisRun.repository_id == repository_id,
            AnalysisRun.pr_number.in_(pr_numbers),
        )
        .order_by(
            AnalysisRun.pr_number.asc(),
            AnalysisRun.created_at.desc(),
            AnalysisRun.id.desc(),
        )
    )
    for run in runs:
        latest_runs_by_pr_number.setdefault(run.pr_number, run)

    return {
        pull_request.number: _review_state_for_pull_request(
            pull_request, latest_runs_by_pr_number.get(pull_request.number)
        )
        for pull_request in pull_requests
    }


def _review_state_for_pull_request(
    pull_request: GitHubPullRequestRead, latest_run: AnalysisRun | None
) -> PullRequestReviewState:
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
