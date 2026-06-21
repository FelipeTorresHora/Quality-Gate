from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.quality_gate_config import QualityGateConfig
from app.models.repository import Repository
from app.schemas.repository import RepositoryCreate


def list_repositories(db: Session) -> list[Repository]:
    return list(db.scalars(select(Repository).order_by(Repository.full_name)))


def get_repository(db: Session, repository_id: UUID) -> Repository:
    repository = db.get(Repository, repository_id)
    if repository is None:
        raise AppError(404, "repository_not_found", "Repository was not found.")
    return repository


def get_repository_by_full_name(db: Session, full_name: str) -> Repository | None:
    return db.scalar(select(Repository).where(Repository.full_name == full_name))


def create_repository(db: Session, payload: RepositoryCreate) -> Repository:
    existing = get_repository_by_full_name(db, payload.full_name or "")
    if existing is not None:
        raise AppError(
            409,
            "repository_already_exists",
            f"Repository {payload.full_name} is already registered.",
        )

    repository = Repository(
        github_repo_id=payload.github_repo_id,
        owner=payload.owner,
        name=payload.name,
        full_name=payload.full_name or f"{payload.owner}/{payload.name}",
        default_branch=payload.default_branch,
    )
    repository.quality_gate_config = QualityGateConfig()
    db.add(repository)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise AppError(
            409,
            "repository_already_exists",
            "Repository already exists or conflicts with an existing GitHub id.",
        ) from exc
    db.refresh(repository)
    return repository
