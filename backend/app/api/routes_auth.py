from fastapi import APIRouter, Depends, Query, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_csrf_token
from app.db.session import get_db
from app.schemas.auth import CurrentUserRead
from app.services import github_oauth_service, session_service
from app.services.session_service import AuthenticatedUser

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/me", response_model=CurrentUserRead)
def get_me(current_user: AuthenticatedUser = Depends(get_current_user)):
    return CurrentUserRead(
        id=current_user.id,
        github_user_id=current_user.github_user_id,
        github_login=current_user.github_login,
        name=current_user.name,
        avatar_url=current_user.avatar_url,
        has_github_connection=current_user.has_github_connection,
    )


@router.get("/github/login")
def github_login(db: Session = Depends(get_db)):
    return RedirectResponse(github_oauth_service.build_login_url(db))


@router.get("/github/callback")
def github_callback(
    code: str = Query(),
    state: str = Query(),
    db: Session = Depends(get_db),
):
    user = github_oauth_service.exchange_code_for_user(code, state, db)
    created = session_service.create_session(db, user)
    settings = session_service.get_settings()
    response = RedirectResponse(settings.frontend_origin)
    session_service.set_session_cookies(response, created)
    return response


@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    _csrf: None = Depends(require_csrf_token),
    db: Session = Depends(get_db),
):
    cookie_value = request.cookies.get(
        session_service.get_settings().session_cookie_name
    )
    session_service.revoke_session(db, cookie_value)
    session_service.clear_session_cookies(response)
    return {"status": "ok"}
