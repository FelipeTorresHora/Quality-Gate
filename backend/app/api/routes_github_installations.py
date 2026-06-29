from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.errors import AppError
from app.db.session import get_db
from app.models.github_app_installation import GitHubAppInstallation
from app.models.user import User
from app.models.user_repository_access import UserRepositoryAccess
from app.schemas.github_installation import (
    GitHubInstallationRead,
    GitHubInstallUrlRead,
)
from app.services import github_installation_service

router = APIRouter(
    prefix="/api/github/installations",
    tags=["github-installations"],
)


@router.get("/install-url", response_model=GitHubInstallUrlRead)
def get_install_url():
    slug = get_settings().github_app_slug
    if not slug:
        raise AppError(
            503,
            "github_app_slug_missing",
            "GITHUB_APP_SLUG is required.",
        )
    return GitHubInstallUrlRead(
        url=f"https://github.com/apps/{slug}/installations/new"
    )


@router.get("", response_model=list[GitHubInstallationRead])
def list_installations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    github_installation_service.sync_user_installations(db, current_user)
    installations = db.scalars(
        select(GitHubAppInstallation)
        .join(
            UserRepositoryAccess,
            UserRepositoryAccess.installation_id == GitHubAppInstallation.id,
        )
        .where(UserRepositoryAccess.user_id == current_user.id)
        .distinct()
        .order_by(
            GitHubAppInstallation.account_login,
            GitHubAppInstallation.installation_id,
        )
    )
    return [
        GitHubInstallationRead(
            installation_id=installation.installation_id,
            account_login=installation.account_login,
            account_type=installation.account_type,
            active=installation.active,
        )
        for installation in installations
    ]
