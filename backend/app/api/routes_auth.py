from fastapi import APIRouter, Depends, Query, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_csrf_token
from app.core.config import get_settings
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import CurrentUserRead
from app.services import github_oauth_service, session_service

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/me", response_model=CurrentUserRead)
def get_me(current_user: User = Depends(get_current_user)):
    return CurrentUserRead(
        id=current_user.id,
        github_user_id=current_user.github_user_id,
        github_login=current_user.github_login,
        name=current_user.name,
        avatar_url=current_user.avatar_url,
        has_github_connection=bool(current_user.github_connections),
    )


@router.get("/github/login")
def github_login():
    return RedirectResponse(github_oauth_service.build_login_url())


@router.get("/github/callback")
def github_callback(
    code: str = Query(),
    state: str = Query(),
    db: Session = Depends(get_db),
):
    user = github_oauth_service.exchange_code_for_user(code, state, db)
    created = session_service.create_session(db, user)
    settings = get_settings()
    response = RedirectResponse(settings.frontend_origin)
    response.set_cookie(
        settings.session_cookie_name,
        created.cookie_value,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite="lax",
        path="/",
    )
    response.set_cookie(
        "qg_csrf",
        created.csrf_token,
        httponly=False,
        secure=settings.session_cookie_secure,
        samesite="lax",
        path="/",
    )
    return response


@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    _csrf: None = Depends(require_csrf_token),
    db: Session = Depends(get_db),
):
    settings = get_settings()
    session_service.revoke_session(
        db,
        request.cookies.get(settings.session_cookie_name),
    )
    response.delete_cookie(settings.session_cookie_name, path="/")
    response.delete_cookie("qg_csrf", path="/")
    return {"status": "ok"}
