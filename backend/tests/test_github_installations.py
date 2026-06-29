from app.core.config import get_settings
from app.models.repository import Repository
from app.models.user import User
from app.models.user_repository_access import UserRepositoryAccess
from app.services import github_installation_service


def test_sync_installation_creates_repository_and_user_access(
    reset_database,
    db_session,
):
    user = User(github_user_id=1, github_login="octocat")
    db_session.add(user)
    db_session.commit()

    installation = github_installation_service.sync_installation_payload(
        db_session,
        user=user,
        installation_payload={
            "id": 99,
            "account": {
                "id": 100,
                "login": "octo-org",
                "type": "Organization",
            },
            "repository_selection": "selected",
            "permissions": {
                "contents": "read",
                "pull_requests": "read",
            },
            "events": ["pull_request"],
        },
        repositories_payload=[
            {
                "id": 456,
                "name": "quality-api",
                "full_name": "octo-org/quality-api",
                "owner": {"login": "octo-org"},
                "default_branch": "main",
                "permissions": {
                    "admin": True,
                    "push": True,
                    "pull": True,
                },
            }
        ],
    )

    assert installation.installation_id == 99
    assert (
        db_session.query(Repository)
        .filter_by(full_name="octo-org/quality-api")
        .count()
        == 1
    )
    assert db_session.query(UserRepositoryAccess).one().is_admin is True


def test_install_url_uses_configured_github_app_slug(monkeypatch, client):
    monkeypatch.setenv("GITHUB_APP_SLUG", "quality-gate-app")
    get_settings.cache_clear()

    response = client.get("/api/github/installations/install-url")

    assert response.status_code == 200
    assert response.json()["url"] == (
        "https://github.com/apps/quality-gate-app/installations/new"
    )
    get_settings.cache_clear()
