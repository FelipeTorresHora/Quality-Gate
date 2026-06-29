from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_csrf_token
from app.db.session import get_db
from app.models.user import User
from app.models.enums import AnalysisRunStatus
from app.schemas.analysis import AnalysisRunDetail
from app.schemas.github import (
    GitHubPullRequestWithReviewState,
    PullRequestContextRead,
)
from app.schemas.repository import RepositoryRead
from app.services import (
    analysis_execution_service,
    analysis_service,
    github_service,
    repository_service,
)
from app.services.github_installation_service import require_repository_access

router = APIRouter(prefix="/api/repositories", tags=["repositories"])


@router.get("", response_model=list[RepositoryRead])
def list_repositories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return repository_service.list_repositories_for_user(db, current_user)


@router.get("/{repository_id}", response_model=RepositoryRead)
def get_repository(
    repository_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_repository_access(db, current_user, repository_id)
    return repository_service.get_repository(db, repository_id)


@router.get(
    "/{repository_id}/pull-requests",
    response_model=list[GitHubPullRequestWithReviewState],
)
def list_pull_requests(
    repository_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_repository_access(db, current_user, repository_id)
    return github_service.list_repository_pull_requests(db, repository_id)


@router.get(
    "/{repository_id}/pull-requests/{pr_number}/context",
    response_model=PullRequestContextRead,
)
def get_pull_request_context(
    repository_id: UUID,
    pr_number: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_repository_access(db, current_user, repository_id)
    return github_service.get_repository_pull_request_context(
        db, repository_id, pr_number
    )


@router.post(
    "/{repository_id}/pull-requests/{pr_number}/analyze",
    response_model=AnalysisRunDetail,
)
def analyze_pull_request(
    repository_id: UUID,
    pr_number: int,
    _csrf: None = Depends(require_csrf_token),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_repository_access(db, current_user, repository_id)
    context = github_service.get_repository_pull_request_context(
        db,
        repository_id,
        pr_number,
    )
    run = analysis_service.create_or_reuse_manual_analysis_run(
        db,
        repository_id,
        context,
    )
    if run.status == AnalysisRunStatus.PENDING:
        return analysis_execution_service.execute_analysis_run(db, run.id)
    return analysis_service.get_analysis_run(db, run.id)
