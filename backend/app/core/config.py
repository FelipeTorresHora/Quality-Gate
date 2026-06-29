from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    app_name: str = "PR Quality Gate Dashboard"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    database_url: str = (
        "postgresql+psycopg://pr_quality:pr_quality@postgres:5432/pr_quality"
    )
    frontend_origin: str = "http://localhost:5173"
    github_app_id: str | None = None
    github_app_client_id: str | None = None
    github_app_client_secret: str | None = None
    github_app_private_key: str | None = None
    github_app_private_key_path: str | None = None
    github_app_slug: str | None = None
    github_api_version: str = "2022-11-28"
    github_token: str | None = None
    github_webhook_secret: str | None = None
    github_default_base_branch: str = "main"
    github_status_context: str = "ai-quality-gate"
    session_secret: str = "development-session-secret"
    session_cookie_name: str = "qg_session"
    session_cookie_secure: bool = False
    token_encryption_key: str | None = None
    auth_callback_url: str = "http://localhost:8000/api/auth/github/callback"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4.1-mini"
    langsmith_tracing: bool = False
    langsmith_api_key: str | None = None
    langsmith_project: str = "pr-quality-dashboard"
    workdir: str = "/tmp/pr-quality-dashboard"
    command_timeout_seconds: int = 600
    keep_workdir: bool = False

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
