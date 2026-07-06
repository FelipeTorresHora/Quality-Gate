from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_csrf_token
from app.core.config import get_settings
from app.db.session import get_db
from app.schemas.quality_gate_config import (
    QualityGateConfigRead,
    QualityGateConfigUpdate,
)
from app.services import quality_gate_service, runtime_cache_service
from app.services.github_installation_service import (
    require_repository_access,
    require_repository_admin,
)
from app.services.session_service import AuthenticatedUser

router = APIRouter(prefix="/api/repositories", tags=["quality-gate-config"])


@router.get(
    "/{repository_id}/quality-gate-config", response_model=QualityGateConfigRead
)
def get_quality_gate_config(
    repository_id: UUID,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    require_repository_access(db, current_user, repository_id)
    settings = get_settings()
    cache_key = f"quality-gate-config:v1:repo:{repository_id}"
    cached = runtime_cache_service.get_json(cache_key)
    if cached is not None:
        return cached

    config = quality_gate_service.get_quality_gate_config(db, repository_id)
    payload = QualityGateConfigRead.model_validate(config).model_dump(mode="json")
    runtime_cache_service.set_json(
        cache_key,
        payload,
        ttl=settings.cache_config_ttl_seconds,
        tags=[f"quality-gate-config:repo:{repository_id}"],
    )
    return payload


@router.put(
    "/{repository_id}/quality-gate-config", response_model=QualityGateConfigRead
)
def update_quality_gate_config(
    repository_id: UUID,
    payload: QualityGateConfigUpdate,
    _csrf: None = Depends(require_csrf_token),
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    require_repository_admin(db, current_user, repository_id)
    config = quality_gate_service.update_quality_gate_config(db, repository_id, payload)
    runtime_cache_service.expire_tags([f"quality-gate-config:repo:{repository_id}"])
    return config
