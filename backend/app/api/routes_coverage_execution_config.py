from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_csrf_token
from app.core.config import get_settings
from app.db.session import get_db
from app.schemas.coverage_execution_config import (
    CoverageExecutionConfigRead,
    CoverageExecutionConfigUpdate,
)
from app.services import coverage_execution_config_service, runtime_cache_service
from app.services.github_installation_service import (
    require_repository_access,
    require_repository_admin,
)
from app.services.session_service import AuthenticatedUser

router = APIRouter(prefix="/api/repositories", tags=["coverage-execution-config"])


@router.get(
    "/{repository_id}/coverage-execution-config",
    response_model=CoverageExecutionConfigRead,
)
def get_coverage_execution_config(
    repository_id: UUID,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    require_repository_access(db, current_user, repository_id)
    settings = get_settings()
    cache_key = f"coverage-config:v1:repo:{repository_id}"
    cached = runtime_cache_service.get_json(cache_key)
    if cached is not None:
        return cached

    config = coverage_execution_config_service.get_coverage_execution_config(
        db,
        repository_id,
    )
    payload = CoverageExecutionConfigRead.model_validate(config).model_dump(
        mode="json"
    )
    runtime_cache_service.set_json(
        cache_key,
        payload,
        ttl=settings.cache_config_ttl_seconds,
        tags=[f"coverage-config:repo:{repository_id}"],
    )
    return payload


@router.put(
    "/{repository_id}/coverage-execution-config",
    response_model=CoverageExecutionConfigRead,
)
def update_coverage_execution_config(
    repository_id: UUID,
    payload: CoverageExecutionConfigUpdate,
    _csrf: None = Depends(require_csrf_token),
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    require_repository_admin(db, current_user, repository_id)
    config = coverage_execution_config_service.update_coverage_execution_config(
        db, repository_id, payload
    )
    runtime_cache_service.expire_tags([f"coverage-config:repo:{repository_id}"])
    return config
