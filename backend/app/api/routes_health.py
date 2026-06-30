import httpx
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError
from app.db.session import get_db
from app.services import github_app_auth_service

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/health/db")
def database_health(db: Session = Depends(get_db)):
    db.execute(text("select 1"))
    return {"status": "ok", "database": "ok"}


@router.get("/health/readiness")
def readiness(db: Session = Depends(get_db)):
    db.execute(text("select 1"))
    settings = get_settings()
    response = httpx.get(
        "https://api.github.com/app",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {github_app_auth_service.generate_app_jwt()}",
            "X-GitHub-Api-Version": settings.github_api_version,
        },
        timeout=20,
    )
    if response.is_error:
        raise AppError(
            503,
            "github_app_credentials_invalid",
            "GitHub App credentials could not be verified.",
        )
    return {"status": "ok", "database": "ok", "github_app": "ok"}
