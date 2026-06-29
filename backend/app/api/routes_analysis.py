from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.analysis import (
    AnalysisRunDetail,
    AnalysisRunSummary,
    GitHubPublicationResult,
)
from app.services import (
    analysis_execution_service,
    analysis_service,
    github_publication_service,
)
from app.services.github_installation_service import (
    require_repository_access,
    require_repository_admin,
)

router = APIRouter(tags=["analysis-runs"])


@router.get(
    "/api/repositories/{repository_id}/analysis-runs",
    response_model=list[AnalysisRunSummary],
)
def list_analysis_runs(
    repository_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_repository_access(db, current_user, repository_id)
    return analysis_service.list_analysis_runs(db, repository_id)


@router.get("/api/analysis-runs/{analysis_run_id}", response_model=AnalysisRunDetail)
def get_analysis_run(
    analysis_run_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    run = analysis_service.get_analysis_run(db, analysis_run_id)
    require_repository_access(db, current_user, run.repository_id)
    return run


@router.post(
    "/api/analysis-runs/{analysis_run_id}/execute",
    response_model=AnalysisRunDetail,
)
def execute_analysis_run(
    analysis_run_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    run = analysis_service.get_analysis_run(db, analysis_run_id)
    require_repository_admin(db, current_user, run.repository_id)
    return analysis_execution_service.execute_analysis_run(db, analysis_run_id)


@router.post(
    "/api/analysis-runs/{analysis_run_id}/publish-github",
    response_model=GitHubPublicationResult,
)
def publish_analysis_run_to_github(
    analysis_run_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    run = analysis_service.get_analysis_run(db, analysis_run_id)
    require_repository_admin(db, current_user, run.repository_id)
    return github_publication_service.publish_analysis_run_to_github(
        db, analysis_run_id
    )
