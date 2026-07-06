from datetime import UTC, datetime
from uuid import UUID

import httpx
from sqlalchemy import delete, or_, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError
from app.models.coverage_execution_config import CoverageExecutionConfig
from app.models.github_app_installation import GitHubAppInstallation
from app.models.github_connection import GitHubConnection
from app.models.installation_repository import InstallationRepository
from app.models.quality_gate_config import QualityGateConfig
from app.models.repository import Repository
from app.models.user import User
from app.models.user_repository_access import UserRepositoryAccess
from app.services import runtime_cache_service, token_crypto_service


def sync_installation_payload(
    db: Session,
    *,
    user: User | None,
    installation_payload: dict,
    repositories_payload: list[dict],
    replace_repositories: bool = True,
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

    current_github_repo_ids = set()
    for repo_payload in repositories_payload:
        current_github_repo_ids.add(int(repo_payload["id"]))
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

        if user is not None and repo_payload.get("permissions"):
            _upsert_user_access(
                db,
                user,
                repository,
                installation,
                repo_payload.get("permissions") or {},
            )

    if replace_repositories:
        _remove_missing_installation_repositories(
            db,
            installation,
            current_github_repo_ids,
        )

    db.commit()
    db.refresh(installation)
    runtime_cache_service.expire_tags(["repositories", "dashboard-summary"])
    return installation


def sync_user_installations(db: Session, user: User) -> None:
    connection = db.scalar(
        select(GitHubConnection)
        .where(
            GitHubConnection.user_id == user.id,
            GitHubConnection.revoked_at.is_(None),
            GitHubConnection.access_token_encrypted.is_not(None),
        )
        .order_by(GitHubConnection.updated_at.desc())
        .limit(1)
    )
    if connection is None or not connection.access_token_encrypted:
        return

    token = token_crypto_service.decrypt_token(connection.access_token_encrypted)
    installations = _get_paginated_user_resource(
        token,
        "/user/installations",
        "installations",
    )
    visible_installation_ids = set()
    for installation_payload in installations:
        installation_id = int(installation_payload["id"])
        visible_installation_ids.add(installation_id)
        repositories_payload = _get_paginated_user_resource(
            token,
            f"/user/installations/{installation_id}/repositories",
            "repositories",
        )
        sync_installation_payload(
            db,
            user=user,
            installation_payload=installation_payload,
            repositories_payload=repositories_payload,
            replace_repositories=False,
        )
        installation = db.scalar(
            select(GitHubAppInstallation).where(
                GitHubAppInstallation.installation_id == installation_id
            )
        )
        if installation is not None:
            _remove_stale_user_repository_access(
                db,
                user,
                installation,
                {int(repository["id"]) for repository in repositories_payload},
            )

    _remove_stale_user_installation_access(
        db,
        user,
        visible_installation_ids,
    )
    db.commit()
    runtime_cache_service.expire_tags(["repositories", "dashboard-summary"])


def deactivate_installation(
    db: Session,
    installation_id: int,
    *,
    suspended_at: datetime | None = None,
    purge: bool = False,
) -> None:
    installation = db.scalar(
        select(GitHubAppInstallation).where(
            GitHubAppInstallation.installation_id == installation_id
        )
    )
    if installation is None:
        return
    installation.active = False
    installation.suspended_at = suspended_at
    if purge:
        db.execute(
            delete(UserRepositoryAccess).where(
                UserRepositoryAccess.installation_id == installation.id
            )
        )
        db.execute(
            delete(InstallationRepository).where(
                InstallationRepository.installation_id == installation.id
            )
        )
    db.commit()
    runtime_cache_service.expire_tags(["repositories", "dashboard-summary"])


def remove_installation_repositories(
    db: Session,
    installation_id: int,
    github_repo_ids: set[int],
) -> None:
    if not github_repo_ids:
        return
    installation = db.scalar(
        select(GitHubAppInstallation).where(
            GitHubAppInstallation.installation_id == installation_id
        )
    )
    if installation is None:
        return
    links = list(
        db.scalars(
            select(InstallationRepository).where(
                InstallationRepository.installation_id == installation.id,
                InstallationRepository.github_repo_id.in_(github_repo_ids),
            )
        )
    )
    for link in links:
        db.execute(
            delete(UserRepositoryAccess).where(
                UserRepositoryAccess.installation_id == installation.id,
                UserRepositoryAccess.repository_id == link.repository_id,
            )
        )
        db.delete(link)
    db.commit()
    runtime_cache_service.expire_tags(["repositories", "dashboard-summary"])


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


def _remove_missing_installation_repositories(
    db: Session,
    installation: GitHubAppInstallation,
    current_github_repo_ids: set[int],
) -> None:
    existing_links = list(
        db.scalars(
            select(InstallationRepository).where(
                InstallationRepository.installation_id == installation.id
            )
        )
    )
    for link in existing_links:
        if link.github_repo_id in current_github_repo_ids:
            continue
        db.execute(
            delete(UserRepositoryAccess).where(
                UserRepositoryAccess.installation_id == installation.id,
                UserRepositoryAccess.repository_id == link.repository_id,
            )
        )
        db.delete(link)


def _remove_stale_user_installation_access(
    db: Session,
    user: User,
    visible_installation_ids: set[int],
) -> None:
    accesses = list(
        db.scalars(
            select(UserRepositoryAccess)
            .join(
                GitHubAppInstallation,
                GitHubAppInstallation.id == UserRepositoryAccess.installation_id,
            )
            .where(UserRepositoryAccess.user_id == user.id)
        )
    )
    for access in accesses:
        if access.installation.installation_id not in visible_installation_ids:
            db.delete(access)


def _remove_stale_user_repository_access(
    db: Session,
    user: User,
    installation: GitHubAppInstallation,
    visible_github_repo_ids: set[int],
) -> None:
    accesses = db.execute(
        select(UserRepositoryAccess, Repository.github_repo_id)
        .join(
            Repository,
            Repository.id == UserRepositoryAccess.repository_id,
        )
        .where(
            UserRepositoryAccess.user_id == user.id,
            UserRepositoryAccess.installation_id == installation.id,
        )
    )
    for access, github_repo_id in accesses:
        if github_repo_id not in visible_github_repo_ids:
            db.delete(access)


def _get_paginated_user_resource(
    token: str,
    path: str,
    collection_key: str,
) -> list[dict]:
    settings = get_settings()
    items: list[dict] = []
    page = 1
    while True:
        response = httpx.get(
            f"https://api.github.com{path}",
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {token}",
                "X-GitHub-Api-Version": settings.github_api_version,
            },
            params={"per_page": 100, "page": page},
            timeout=20,
        )
        if response.is_error:
            raise AppError(
                502,
                "github_installation_sync_failed",
                "GitHub App installations could not be synchronized.",
            )
        page_items = response.json().get(collection_key) or []
        items.extend(page_items)
        if len(page_items) < 100:
            return items
        page += 1


def require_repository_access(
    db: Session,
    user: User,
    repository_id: UUID,
) -> UserRepositoryAccess:
    access = db.scalar(
        select(UserRepositoryAccess)
        .join(
            GitHubAppInstallation,
            GitHubAppInstallation.id == UserRepositoryAccess.installation_id,
        )
        .where(
            UserRepositoryAccess.user_id == user.id,
            UserRepositoryAccess.repository_id == repository_id,
            GitHubAppInstallation.active.is_(True),
            GitHubAppInstallation.suspended_at.is_(None),
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


def get_active_installation_for_repository(
    db: Session,
    repository_id: UUID,
) -> InstallationRepository:
    link = db.scalar(
        select(InstallationRepository)
        .join(
            GitHubAppInstallation,
            GitHubAppInstallation.id
            == InstallationRepository.installation_id,
        )
        .where(
            InstallationRepository.repository_id == repository_id,
            GitHubAppInstallation.active.is_(True),
            GitHubAppInstallation.suspended_at.is_(None),
        )
        .limit(1)
    )
    if link is None:
        raise AppError(
            409,
            "github_installation_required",
            "An active GitHub App installation is required.",
        )
    return link
