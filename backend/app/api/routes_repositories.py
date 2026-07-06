from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_csrf_token
from app.core.config import get_settings
from app.db.session import get_db
from app.models.enums import AnalysisRunStatus
from app.schemas.analysis import AnalysisRunDetail
from app.schemas.github import (
    GitHubPullRequestWithReviewState,
    PullRequestContextRead,
)
from app.schemas.repository import RepositoryRead
from app.services import (
    analysis_queue,
    analysis_service,
    github_service,
    repository_service,
    runtime_cache_service,
)
from app.services.github_installation_service import require_repository_access
from app.services.session_service import AuthenticatedUser

router = APIRouter(prefix="/api/repositories", tags=["repositories"])


@router.get("", response_model=list[RepositoryRead])
def list_repositories(
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    settings = get_settings()
    cache_key = f"repositories:v1:user:{current_user.id}"
    cached = runtime_cache_service.get_json(cache_key)
    if cached is not None:
        return cached

    repositories = repository_service.list_repositories_for_user(db, current_user)
    payload = [
        RepositoryRead.model_validate(repository).model_dump(mode="json")
        for repository in repositories
    ]
    runtime_cache_service.set_json(
        cache_key,
        payload,
        ttl=settings.cache_repository_list_ttl_seconds,
        tags=["repositories", f"user:{current_user.id}"],
    )
    return payload


@router.get("/{repository_id}", response_model=RepositoryRead)
def get_repository(
    repository_id: UUID,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    require_repository_access(db, current_user, repository_id)
    settings = get_settings()
    cache_key = f"repository:v1:{repository_id}"
    cached = runtime_cache_service.get_json(cache_key)
    if cached is not None:
        return cached

    repository = repository_service.get_repository(db, repository_id)
    payload = RepositoryRead.model_validate(repository).model_dump(mode="json")
    runtime_cache_service.set_json(
        cache_key,
        payload,
        ttl=settings.cache_repository_detail_ttl_seconds,
        tags=[f"repository:{repository_id}"],
    )
    return payload


@router.get(
    "/{repository_id}/pull-requests",
    response_model=list[GitHubPullRequestWithReviewState],
)
def list_pull_requests(
    repository_id: UUID,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    require_repository_access(db, current_user, repository_id)
    settings = get_settings()
    cache_key = f"pull-requests:v1:repo:{repository_id}"
    cached = runtime_cache_service.get_json(cache_key)
    if cached is not None:
        return cached

    pull_requests = github_service.list_repository_pull_requests(db, repository_id)
    payload = [
        pull_request.model_dump(mode="json") for pull_request in pull_requests
    ]
    runtime_cache_service.set_json(
        cache_key,
        payload,
        ttl=settings.cache_pull_request_list_ttl_seconds,
        tags=[f"pull-requests:repo:{repository_id}"],
    )
    return payload


@router.get(
    "/{repository_id}/pull-requests/{pr_number}/context",
    response_model=PullRequestContextRead,
)
def get_pull_request_context(
    repository_id: UUID,
    pr_number: int,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    require_repository_access(db, current_user, repository_id)
    return github_service.get_repository_pull_request_context(
        db, repository_id, pr_number
    )


@router.post(
    "/{repository_id}/pull-requests/{pr_number}/analyze",
    response_model=AnalysisRunDetail,
    status_code=202,
)
def analyze_pull_request(
    repository_id: UUID,
    pr_number: int,
    _csrf: None = Depends(require_csrf_token),
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
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
        analysis_queue.enqueue(run.id)
    runtime_cache_service.expire_tags(
        [
            f"analysis-runs:repo:{repository_id}",
            f"pull-requests:repo:{repository_id}",
            "dashboard-summary",
        ]
    )
    return analysis_service.get_analysis_run(db, run.id)
