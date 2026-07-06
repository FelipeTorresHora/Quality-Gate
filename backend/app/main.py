from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    routes_analysis,
    routes_auth,
    routes_coverage_execution_config,
    routes_dashboard,
    routes_github_installations,
    routes_github_webhooks,
    routes_health,
    routes_quality_gate,
    routes_repositories,
)
from app.core.config import get_settings, validate_runtime_security_settings
from app.core.errors import AppError, app_error_handler

settings = get_settings()
validate_runtime_security_settings(settings)

app = FastAPI(title=settings.app_name)
app.add_exception_handler(AppError, app_error_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes_health.router)
app.include_router(routes_auth.router)
app.include_router(routes_dashboard.router)
app.include_router(routes_repositories.router)
app.include_router(routes_quality_gate.router)
app.include_router(routes_coverage_execution_config.router)
app.include_router(routes_analysis.router)
app.include_router(routes_github_installations.router)
app.include_router(routes_github_webhooks.router)
