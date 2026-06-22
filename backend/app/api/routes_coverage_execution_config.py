from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.coverage_execution_config import (
    CoverageExecutionConfigRead,
    CoverageExecutionConfigUpdate,
)
from app.services import coverage_execution_config_service

router = APIRouter(prefix="/api/repositories", tags=["coverage-execution-config"])


@router.get(
    "/{repository_id}/coverage-execution-config",
    response_model=CoverageExecutionConfigRead,
)
def get_coverage_execution_config(repository_id: UUID, db: Session = Depends(get_db)):
    return coverage_execution_config_service.get_coverage_execution_config(
        db, repository_id
    )


@router.put(
    "/{repository_id}/coverage-execution-config",
    response_model=CoverageExecutionConfigRead,
)
def update_coverage_execution_config(
    repository_id: UUID,
    payload: CoverageExecutionConfigUpdate,
    db: Session = Depends(get_db),
):
    return coverage_execution_config_service.update_coverage_execution_config(
        db, repository_id, payload
    )
