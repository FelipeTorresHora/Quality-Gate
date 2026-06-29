from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.quality_gate_config import (
    QualityGateConfigRead,
    QualityGateConfigUpdate,
)
from app.services import quality_gate_service
from app.services.github_installation_service import (
    require_repository_access,
    require_repository_admin,
)

router = APIRouter(prefix="/api/repositories", tags=["quality-gate-config"])


@router.get(
    "/{repository_id}/quality-gate-config", response_model=QualityGateConfigRead
)
def get_quality_gate_config(
    repository_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_repository_access(db, current_user, repository_id)
    return quality_gate_service.get_quality_gate_config(db, repository_id)


@router.put(
    "/{repository_id}/quality-gate-config", response_model=QualityGateConfigRead
)
def update_quality_gate_config(
    repository_id: UUID,
    payload: QualityGateConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_repository_admin(db, current_user, repository_id)
    return quality_gate_service.update_quality_gate_config(db, repository_id, payload)
