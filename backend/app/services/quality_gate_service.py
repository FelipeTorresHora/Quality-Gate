from uuid import UUID

from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.quality_gate_config import QualityGateConfig
from app.schemas.quality_gate_config import QualityGateConfigUpdate
from app.services.repository_service import get_repository


def get_quality_gate_config(db: Session, repository_id: UUID) -> QualityGateConfig:
    repository = get_repository(db, repository_id)
    if repository.quality_gate_config is None:
        raise AppError(
            404,
            "quality_gate_config_not_found",
            "Quality gate config was not found for this repository.",
        )
    return repository.quality_gate_config


def update_quality_gate_config(
    db: Session, repository_id: UUID, payload: QualityGateConfigUpdate
) -> QualityGateConfig:
    config = get_quality_gate_config(db, repository_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(config, field, value)
    db.commit()
    db.refresh(config)
    return config
