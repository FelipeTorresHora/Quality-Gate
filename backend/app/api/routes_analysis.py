from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.analysis import (
    AnalysisRunDetail,
    AnalysisRunSummary,
    MockAnalysisRunCreate,
)
from app.services import analysis_service

router = APIRouter(tags=["analysis-runs"])


@router.get(
    "/api/repositories/{repository_id}/analysis-runs",
    response_model=list[AnalysisRunSummary],
)
def list_analysis_runs(repository_id: UUID, db: Session = Depends(get_db)):
    return analysis_service.list_analysis_runs(db, repository_id)


@router.post(
    "/api/repositories/{repository_id}/analysis-runs/mock",
    response_model=AnalysisRunDetail,
    status_code=status.HTTP_201_CREATED,
)
def create_mock_analysis_run(
    repository_id: UUID,
    payload: MockAnalysisRunCreate,
    db: Session = Depends(get_db),
):
    return analysis_service.create_mock_analysis_run(db, repository_id, payload)


@router.get("/api/analysis-runs/{analysis_run_id}", response_model=AnalysisRunDetail)
def get_analysis_run(analysis_run_id: UUID, db: Session = Depends(get_db)):
    return analysis_service.get_analysis_run(db, analysis_run_id)
