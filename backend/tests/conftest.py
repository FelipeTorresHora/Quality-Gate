import os
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

os.environ["DATABASE_URL"] = (
    os.environ.get("TEST_DATABASE_URL")
    or "postgresql+psycopg://pr_quality:pr_quality@localhost:55432/pr_quality_test"
)
os.environ.setdefault("PR_QUALITY_ENV_FILE", "")

from app.db.base import Base  # noqa: E402
from app.db.session import engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture
def reset_database():
    try:
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
    except OperationalError as exc:
        pytest.skip(f"PostgreSQL test database is not available: {exc}")
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(reset_database):
    from app.db.session import SessionLocal

    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def create_user_repo_access(db_session):
    from app.models.github_app_installation import GitHubAppInstallation
    from app.models.repository import Repository
    from app.models.user import User
    from app.models.user_repository_access import UserRepositoryAccess
    from app.services import session_service

    def create(*, is_admin: bool):
        user = User(
            github_user_id=10 if is_admin else 11,
            github_login="admin" if is_admin else "viewer",
        )
        repository = Repository(
            github_repo_id=200,
            owner="octo-org",
            name="quality-api",
            full_name="octo-org/quality-api",
            default_branch="main",
        )
        installation = GitHubAppInstallation(
            installation_id=300,
            account_id=400,
            account_login="octo-org",
            account_type="Organization",
            permissions_json={},
            events_json=[],
            active=True,
        )
        db_session.add_all([user, repository, installation])
        db_session.flush()
        db_session.add(
            UserRepositoryAccess(
                user_id=user.id,
                repository_id=repository.id,
                installation_id=installation.id,
                permission="admin" if is_admin else "pull",
                is_admin=is_admin,
                synced_at=datetime.now(UTC),
            )
        )
        db_session.commit()
        created = session_service.create_session(db_session, user)
        return user, repository, created.cookie_value, created.csrf_token

    return create


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def repository(client, reset_database, db_session, monkeypatch):
    from app.models.repository import Repository
    from app.models.user import User
    from app.services import (
        github_app_auth_service,
        github_installation_service,
        session_service,
    )

    user = User(github_user_id=9001, github_login="test-admin")
    db_session.add(user)
    db_session.commit()
    github_installation_service.sync_installation_payload(
        db_session,
        user=user,
        installation_payload={
            "id": 9002,
            "account": {
                "id": 9003,
                "login": "horinha04",
                "type": "Organization",
            },
            "repository_selection": "selected",
            "permissions": {
                "contents": "read",
                "pull_requests": "write",
                "statuses": "write",
            },
            "events": ["pull_request"],
        },
        repositories_payload=[
            {
                "id": 9004,
                "owner": {"login": "horinha04"},
                "name": "meu-projeto",
                "full_name": "horinha04/meu-projeto",
                "default_branch": "main",
                "permissions": {
                    "admin": True,
                    "push": True,
                    "pull": True,
                },
            }
        ],
    )
    repository = db_session.query(Repository).filter_by(
        full_name="horinha04/meu-projeto"
    ).one()
    created = session_service.create_session(db_session, user)
    client.cookies.set("qg_session", created.cookie_value)
    client.cookies.set("qg_csrf", created.csrf_token)
    monkeypatch.setattr(
        github_app_auth_service,
        "generate_installation_token",
        lambda installation_id: f"installation-token-{installation_id}",
    )
    return {
        "id": str(repository.id),
        "github_repo_id": repository.github_repo_id,
        "owner": repository.owner,
        "name": repository.name,
        "full_name": repository.full_name,
        "default_branch": repository.default_branch,
        "csrf_token": created.csrf_token,
    }
