from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.db.session import get_db
from app.schemas.dashboard import DashboardSummaryRead
from app.services import dashboard_service, runtime_cache_service
from app.services.session_service import AuthenticatedUser

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummaryRead)
def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    settings = get_settings()
    cache_key = f"dashboard-summary:v1:user:{current_user.id}"
    cached = runtime_cache_service.get_json(cache_key)
    if cached is not None:
        return cached

    summary = dashboard_service.get_dashboard_summary(db, current_user)
    payload = summary.model_dump(mode="json")
    runtime_cache_service.set_json(
        cache_key,
        payload,
        ttl=settings.cache_dashboard_ttl_seconds,
        tags=["dashboard-summary", f"user:{current_user.id}"],
    )
    return payload
