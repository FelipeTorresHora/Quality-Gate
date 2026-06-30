from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError
from app.db.session import get_db
from app.models.user import User
from app.services import session_service


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    cookie_name = get_settings().session_cookie_name
    cookie_value = request.cookies.get(cookie_name)
    user = session_service.get_user_for_session(db, cookie_value)
    if user is None:
        raise AppError(
            401,
            "authentication_required",
            "Authentication is required.",
        )
    return user


def require_csrf_token(
    request: Request,
    db: Session = Depends(get_db),
) -> None:
    settings = get_settings()
    session_cookie = request.cookies.get(settings.session_cookie_name)
    if not session_cookie:
        return
    if session_service.get_active_session(db, session_cookie) is None:
        return

    csrf_header = request.headers.get("X-CSRF-Token")
    csrf_cookie = request.cookies.get("qg_csrf")
    if (
        not csrf_header
        or not csrf_cookie
        or csrf_header != csrf_cookie
        or not session_service.validate_csrf_token(db, session_cookie, csrf_header)
    ):
        raise AppError(
            403,
            "csrf_token_invalid",
            "CSRF token is invalid or missing.",
        )
