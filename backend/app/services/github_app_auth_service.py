from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
import jwt

from app.core.config import get_settings
from app.core.errors import AppError

INSTALLATION_TOKEN_CACHE: dict[int, tuple[str, datetime]] = {}


def _private_key() -> str:
    settings = get_settings()
    if settings.github_app_private_key:
        return settings.github_app_private_key.replace("\\n", "\n")
    if settings.github_app_private_key_path:
        return Path(settings.github_app_private_key_path).read_text(encoding="utf-8")
    raise AppError(
        503,
        "github_app_config_missing",
        "github_app_private_key or github_app_private_key_path is required.",
    )


def generate_app_jwt() -> str:
    settings = get_settings()
    if not settings.github_app_id:
        raise AppError(
            503,
            "github_app_config_missing",
            "GITHUB_APP_ID is required.",
        )
    now = datetime.now(UTC)
    payload = {
        "iat": int((now - timedelta(seconds=60)).timestamp()),
        "exp": int((now + timedelta(minutes=10)).timestamp()),
        "iss": settings.github_app_id,
    }
    try:
        return jwt.encode(payload, _private_key(), algorithm="RS256")
    except AppError:
        raise
    except Exception as exc:
        raise AppError(
            503,
            "github_app_jwt_failed",
            "GitHub App JWT could not be generated.",
        ) from exc


def generate_installation_token(installation_id: int) -> str:
    cached = INSTALLATION_TOKEN_CACHE.get(installation_id)
    if cached and cached[1] > datetime.now(UTC) + timedelta(minutes=5):
        return cached[0]

    settings = get_settings()
    response = httpx.post(
        f"https://api.github.com/app/installations/{installation_id}/access_tokens",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {generate_app_jwt()}",
            "X-GitHub-Api-Version": settings.github_api_version,
        },
        timeout=20,
    )
    if response.is_error:
        raise AppError(
            503,
            "github_installation_token_failed",
            "GitHub installation token could not be generated.",
        )
    payload = response.json()
    token = payload["token"]
    expires_at = datetime.fromisoformat(
        payload["expires_at"].replace("Z", "+00:00")
    )
    INSTALLATION_TOKEN_CACHE[installation_id] = (token, expires_at)
    return token
