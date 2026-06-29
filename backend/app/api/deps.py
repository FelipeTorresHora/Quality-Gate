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
