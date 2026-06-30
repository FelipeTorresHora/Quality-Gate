from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_csrf_token
from app.db.session import get_db
from app.models.user import User
from app.schemas.coverage_execution_config import (
    CoverageExecutionConfigRead,
    CoverageExecutionConfigUpdate,
)
from app.services import coverage_execution_config_service
from app.services.github_installation_service import (
    require_repository_access,
    require_repository_admin,
)

router = APIRouter(prefix="/api/repositories", tags=["coverage-execution-config"])


@router.get(
    "/{repository_id}/coverage-execution-config",
    response_model=CoverageExecutionConfigRead,
)
def get_coverage_execution_config(
    repository_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_repository_access(db, current_user, repository_id)
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
    _csrf: None = Depends(require_csrf_token),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_repository_admin(db, current_user, repository_id)
    return coverage_execution_config_service.update_coverage_execution_config(
        db, repository_id, payload
    )
