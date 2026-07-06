from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import hashlib
import hmac
import secrets
from uuid import UUID

import jwt
from jwt import InvalidTokenError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.user import User


@dataclass
class CreatedSession:
    cookie_value: str
    csrf_token: str
    expires_at: datetime
    session: None = None


@dataclass(frozen=True)
class AuthenticatedUser:
    id: UUID
    github_user_id: int
    github_login: str
    name: str | None
    avatar_url: str | None
    has_github_connection: bool


def _hash_token(value: str) -> str:
    secret = get_settings().session_secret.encode("utf-8")
    return hmac.new(secret, value.encode("utf-8"), hashlib.sha256).hexdigest()


def create_session(
    db: Session,
    user: User,
    *,
    ttl: timedelta | None = None,
) -> CreatedSession:
    _ = db
    settings = get_settings()
    ttl = ttl or timedelta(seconds=settings.session_ttl_seconds)
    csrf_token = secrets.token_urlsafe(32)
    now = datetime.now(UTC)
    expires_at = now + ttl
    payload = {
        "sub": str(user.id),
        "github_user_id": user.github_user_id,
        "github_login": user.github_login,
        "name": user.name,
        "avatar_url": user.avatar_url,
        "has_github_connection": bool(user.github_connections),
        "csrf_hash": _hash_token(csrf_token),
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    cookie_value = jwt.encode(
        payload,
        settings.session_secret,
        algorithm="HS256",
    )
    return CreatedSession(
        cookie_value=cookie_value,
        csrf_token=csrf_token,
        expires_at=expires_at,
    )


def get_user_for_session(cookie_value: str | None) -> AuthenticatedUser | None:
    payload = _decode_session(cookie_value)
    if payload is None:
        return None
    try:
        return AuthenticatedUser(
            id=UUID(str(payload["sub"])),
            github_user_id=int(payload["github_user_id"]),
            github_login=str(payload["github_login"]),
            name=payload.get("name"),
            avatar_url=payload.get("avatar_url"),
            has_github_connection=bool(payload.get("has_github_connection")),
        )
    except (KeyError, TypeError, ValueError):
        return None


def validate_csrf_token(
    cookie_value: str | None,
    csrf_token: str | None,
) -> bool:
    if not csrf_token:
        return False
    payload = _decode_session(cookie_value)
    csrf_hash = payload.get("csrf_hash") if payload else None
    if not csrf_hash:
        return False
    return hmac.compare_digest(str(csrf_hash), _hash_token(csrf_token))


def revoke_session(db: Session, cookie_value: str | None) -> None:
    _ = (db, cookie_value)


def _decode_session(cookie_value: str | None) -> dict | None:
    if not cookie_value:
        return None
    try:
        payload = jwt.decode(
            cookie_value,
            get_settings().session_secret,
            algorithms=["HS256"],
        )
    except InvalidTokenError:
        return None
    if not isinstance(payload, dict):
        return None
    return payload
