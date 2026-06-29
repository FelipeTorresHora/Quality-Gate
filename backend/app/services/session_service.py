from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import hashlib
import hmac
import secrets

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.user import User
from app.models.user_session import UserSession


@dataclass
class CreatedSession:
    session: UserSession
    cookie_value: str
    csrf_token: str


def _hash_token(value: str) -> str:
    secret = get_settings().session_secret.encode("utf-8")
    return hmac.new(secret, value.encode("utf-8"), hashlib.sha256).hexdigest()


def create_session(
    db: Session,
    user: User,
    *,
    ttl: timedelta = timedelta(hours=8),
) -> CreatedSession:
    cookie_value = secrets.token_urlsafe(48)
    csrf_token = secrets.token_urlsafe(32)
    now = datetime.now(UTC)
    session = UserSession(
        user_id=user.id,
        session_token_hash=_hash_token(cookie_value),
        csrf_token_hash=_hash_token(csrf_token),
        expires_at=now + ttl,
        last_seen_at=now,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return CreatedSession(
        session=session,
        cookie_value=cookie_value,
        csrf_token=csrf_token,
    )


def get_user_for_session(db: Session, cookie_value: str | None) -> User | None:
    if not cookie_value:
        return None
    session = db.scalar(
        select(UserSession).where(
            UserSession.session_token_hash == _hash_token(cookie_value)
        )
    )
    if session is None:
        return None
    if session.revoked_at is not None or session.expires_at <= datetime.now(UTC):
        return None
    session.last_seen_at = datetime.now(UTC)
    db.commit()
    return db.get(User, session.user_id)


def revoke_session(db: Session, cookie_value: str | None) -> None:
    if not cookie_value:
        return
    session = db.scalar(
        select(UserSession).where(
            UserSession.session_token_hash == _hash_token(cookie_value)
        )
    )
    if session is None:
        return
    session.revoked_at = datetime.now(UTC)
    db.commit()
