from dataclasses import dataclass
from datetime import UTC, datetime
import secrets
from urllib.parse import urlencode

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError
from app.models.github_connection import GitHubConnection
from app.models.user import User
from app.services import token_crypto_service

AUTH_STATES: dict[str, str] = {}


@dataclass
class OAuthState:
    state: str
    verifier: str


def build_login_url() -> str:
    settings = get_settings()
    if not settings.github_app_client_id:
        raise AppError(
            503,
            "github_app_config_missing",
            "GITHUB_APP_CLIENT_ID is required.",
        )
    state = secrets.token_urlsafe(32)
    verifier = secrets.token_urlsafe(48)
    AUTH_STATES[state] = verifier
    query = urlencode(
        {
            "client_id": settings.github_app_client_id,
            "redirect_uri": settings.auth_callback_url,
            "state": state,
        }
    )
    return f"https://github.com/login/oauth/authorize?{query}"


def exchange_code_for_user(code: str, state: str, db: Session) -> User:
    if state not in AUTH_STATES:
        raise AppError(
            400,
            "github_oauth_state_invalid",
            "GitHub OAuth state is invalid.",
        )
    AUTH_STATES.pop(state, None)
    settings = get_settings()
    response = httpx.post(
        "https://github.com/login/oauth/access_token",
        headers={"Accept": "application/json"},
        data={
            "client_id": settings.github_app_client_id,
            "client_secret": settings.github_app_client_secret,
            "code": code,
            "redirect_uri": settings.auth_callback_url,
        },
        timeout=20,
    )
    if response.is_error:
        raise AppError(
            502,
            "github_oauth_exchange_failed",
            "GitHub OAuth exchange failed.",
        )
    token = response.json().get("access_token")
    if not token:
        raise AppError(
            502,
            "github_oauth_exchange_failed",
            "GitHub OAuth exchange failed.",
        )
    user_response = httpx.get(
        "https://api.github.com/user",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": settings.github_api_version,
        },
        timeout=20,
    )
    if user_response.is_error:
        raise AppError(
            502,
            "github_oauth_exchange_failed",
            "GitHub user identity could not be read.",
        )
    return upsert_user_from_github(db, user_response.json(), token)


def upsert_user_from_github(
    db: Session,
    payload: dict,
    access_token: str,
) -> User:
    user = db.scalar(
        select(User).where(User.github_user_id == int(payload["id"]))
    )
    if user is None:
        user = User(
            github_user_id=int(payload["id"]),
            github_login=payload["login"],
        )
        db.add(user)
    user.github_login = payload["login"]
    user.name = payload.get("name")
    user.email = payload.get("email")
    user.avatar_url = payload.get("avatar_url")
    user.last_login_at = datetime.now(UTC)
    db.flush()

    connection = db.scalar(
        select(GitHubConnection).where(GitHubConnection.user_id == user.id)
    )
    if connection is None:
        connection = GitHubConnection(
            user_id=user.id,
            github_user_id=user.github_user_id,
            github_login=user.github_login,
        )
        db.add(connection)
    connection.github_user_id = user.github_user_id
    connection.github_login = user.github_login

    connection.access_token_encrypted = token_crypto_service.encrypt_token(
        access_token
    )
    db.commit()
    db.refresh(user)
    return user
