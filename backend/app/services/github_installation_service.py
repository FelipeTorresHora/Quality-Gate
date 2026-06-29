from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.coverage_execution_config import CoverageExecutionConfig
from app.models.github_app_installation import GitHubAppInstallation
from app.models.installation_repository import InstallationRepository
from app.models.quality_gate_config import QualityGateConfig
from app.models.repository import Repository
from app.models.user import User
from app.models.user_repository_access import UserRepositoryAccess


def sync_installation_payload(
    db: Session,
    *,
    user: User | None,
    installation_payload: dict,
    repositories_payload: list[dict],
) -> GitHubAppInstallation:
    installation = db.scalar(
        select(GitHubAppInstallation).where(
            GitHubAppInstallation.installation_id
            == int(installation_payload["id"])
        )
    )
    if installation is None:
        installation = GitHubAppInstallation(
            installation_id=int(installation_payload["id"])
        )
        db.add(installation)

    account = installation_payload["account"]
    installation.account_id = int(account["id"])
    installation.account_login = account["login"]
    installation.account_type = account["type"]
    installation.repository_selection = installation_payload.get(
        "repository_selection"
    )
    installation.permissions_json = (
        installation_payload.get("permissions") or {}
    )
    installation.events_json = installation_payload.get("events") or []
    installation.active = True
    installation.suspended_at = None
    db.flush()

    for repo_payload in repositories_payload:
        repository = _upsert_repository(db, repo_payload)
        link = db.scalar(
            select(InstallationRepository).where(
                InstallationRepository.installation_id == installation.id,
                InstallationRepository.repository_id == repository.id,
            )
        )
        if link is None:
            link = InstallationRepository(
                installation_id=installation.id,
                repository_id=repository.id,
                github_repo_id=repository.github_repo_id,
                full_name=repository.full_name,
            )
            db.add(link)
        else:
            link.github_repo_id = repository.github_repo_id
            link.full_name = repository.full_name

        if user is not None:
            _upsert_user_access(
                db,
                user,
                repository,
                installation,
                repo_payload.get("permissions") or {},
            )

    db.commit()
    db.refresh(installation)
    return installation


def _upsert_repository(db: Session, payload: dict) -> Repository:
    github_repo_id = int(payload["id"])
    repository = db.scalar(
        select(Repository).where(
            or_(
                Repository.github_repo_id == github_repo_id,
                Repository.full_name == payload["full_name"],
            )
        )
    )
    if repository is None:
        repository = Repository(github_repo_id=github_repo_id)
        repository.quality_gate_config = QualityGateConfig()
        repository.coverage_execution_config = CoverageExecutionConfig()
        db.add(repository)
    repository.github_repo_id = github_repo_id
    repository.owner = payload["owner"]["login"]
    repository.name = payload["name"]
    repository.full_name = payload["full_name"]
    repository.default_branch = payload.get("default_branch") or "main"
    db.flush()
    return repository


def _upsert_user_access(
    db: Session,
    user: User,
    repository: Repository,
    installation: GitHubAppInstallation,
    permissions: dict,
) -> UserRepositoryAccess:
    access = db.scalar(
        select(UserRepositoryAccess).where(
            UserRepositoryAccess.user_id == user.id,
            UserRepositoryAccess.repository_id == repository.id,
        )
    )
    if access is None:
        access = UserRepositoryAccess(
            user_id=user.id,
            repository_id=repository.id,
            installation_id=installation.id,
        )
        db.add(access)
    access.installation_id = installation.id
    access.permission = _permission_name(permissions)
    access.is_admin = bool(permissions.get("admin"))
    access.synced_at = datetime.now(UTC)
    return access


def _permission_name(permissions: dict) -> str | None:
    for name in ("admin", "maintain", "push", "triage", "pull"):
        if permissions.get(name):
            return name
    return None


def require_repository_access(
    db: Session,
    user: User,
    repository_id: UUID,
) -> UserRepositoryAccess:
    access = db.scalar(
        select(UserRepositoryAccess).where(
            UserRepositoryAccess.user_id == user.id,
            UserRepositoryAccess.repository_id == repository_id,
        )
    )
    if access is None:
        raise AppError(
            403,
            "repository_access_denied",
            "You do not have access to this repository.",
        )
    return access


def require_repository_admin(
    db: Session,
    user: User,
    repository_id: UUID,
) -> UserRepositoryAccess:
    access = require_repository_access(db, user, repository_id)
    if not access.is_admin:
        raise AppError(
            403,
            "repository_admin_required",
            "Repository admin permission is required.",
        )
    return access
