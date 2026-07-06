from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_csrf_token
from app.core.config import get_settings
from app.db.session import get_db
from app.schemas.analysis import (
    AnalysisRunDetail,
    AnalysisRunSummary,
    GitHubPublicationResult,
)
from app.services import (
    analysis_queue,
    analysis_service,
    github_publication_service,
    runtime_cache_service,
)
from app.services.github_installation_service import (
    require_repository_access,
    require_repository_admin,
)
from app.services.session_service import AuthenticatedUser

router = APIRouter(tags=["analysis-runs"])


@router.get(
    "/api/repositories/{repository_id}/analysis-runs",
    response_model=list[AnalysisRunSummary],
)
def list_analysis_runs(
    repository_id: UUID,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    require_repository_access(db, current_user, repository_id)
    settings = get_settings()
    cache_key = f"analysis-runs:v1:repo:{repository_id}"
    cached = runtime_cache_service.get_json(cache_key)
    if cached is not None:
        return cached

    runs = analysis_service.list_analysis_runs(db, repository_id)
    payload = [
        AnalysisRunSummary.model_validate(run).model_dump(mode="json")
        for run in runs
    ]
    runtime_cache_service.set_json(
        cache_key,
        payload,
        ttl=settings.cache_analysis_run_list_ttl_seconds,
        tags=[f"analysis-runs:repo:{repository_id}"],
    )
    return payload


@router.get("/api/analysis-runs/{analysis_run_id}", response_model=AnalysisRunDetail)
def get_analysis_run(
    analysis_run_id: UUID,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    run = analysis_service.get_analysis_run(db, analysis_run_id)
    require_repository_access(db, current_user, run.repository_id)
    return run


@router.post(
    "/api/analysis-runs/{analysis_run_id}/execute",
    response_model=AnalysisRunDetail,
    status_code=202,
)
def execute_analysis_run(
    analysis_run_id: UUID,
    _csrf: None = Depends(require_csrf_token),
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    run = analysis_service.get_analysis_run(db, analysis_run_id)
    require_repository_admin(db, current_user, run.repository_id)
    analysis_queue.enqueue(analysis_run_id)
    runtime_cache_service.expire_tags(
        [
            f"analysis-runs:repo:{run.repository_id}",
            f"pull-requests:repo:{run.repository_id}",
            "dashboard-summary",
        ]
    )
    return analysis_service.get_analysis_run(db, analysis_run_id)


@router.post(
    "/api/analysis-runs/{analysis_run_id}/publish-github",
    response_model=GitHubPublicationResult,
)
def publish_analysis_run_to_github(
    analysis_run_id: UUID,
    _csrf: None = Depends(require_csrf_token),
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    run = analysis_service.get_analysis_run(db, analysis_run_id)
    require_repository_admin(db, current_user, run.repository_id)
    return github_publication_service.publish_analysis_run_to_github(
        db, analysis_run_id
    )
