from app.core.config import get_settings
from app.models.github_connection import GitHubConnection
from app.models.installation_repository import InstallationRepository
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


def test_list_installations_refreshes_current_user_installations(
    monkeypatch,
    client,
    repository,
):
    refreshed = []
    monkeypatch.setattr(
        github_installation_service,
        "sync_user_installations",
        lambda db, user: refreshed.append(user.github_login),
    )

    response = client.get("/api/github/installations")

    assert response.status_code == 200
    assert refreshed == ["test-admin"]


def test_user_installation_resource_paginates_with_oauth_token(monkeypatch):
    calls = []
    pages = [
        {"installations": [{"id": index} for index in range(100)]},
        {"installations": [{"id": 100}]},
    ]

    class Response:
        is_error = False

        def __init__(self, payload):
            self.payload = payload

        def json(self):
            return self.payload

    def fake_get(url, *, headers, params, timeout):
        calls.append((url, headers, params, timeout))
        return Response(pages.pop(0))

    monkeypatch.setattr(github_installation_service.httpx, "get", fake_get)

    result = github_installation_service._get_paginated_user_resource(
        "oauth-token",
        "/user/installations",
        "installations",
    )

    assert len(result) == 101
    assert [call[2]["page"] for call in calls] == [1, 2]
    assert calls[0][1]["Authorization"] == "Bearer oauth-token"


def test_user_sync_only_reconciles_current_users_repository_access(
    monkeypatch,
    reset_database,
    db_session,
):
    current_user = User(github_user_id=1, github_login="current-user")
    other_user = User(github_user_id=2, github_login="other-user")
    db_session.add_all([current_user, other_user])
    db_session.flush()
    db_session.add(
        GitHubConnection(
            user_id=current_user.id,
            github_user_id=current_user.github_user_id,
            github_login=current_user.github_login,
            access_token_encrypted="encrypted-token",
        )
    )
    db_session.commit()

    installation_payload = {
        "id": 99,
        "account": {
            "id": 100,
            "login": "octo-org",
            "type": "Organization",
        },
        "repository_selection": "selected",
        "permissions": {"contents": "read"},
        "events": ["pull_request"],
    }
    repositories = [
        {
            "id": 456,
            "name": "quality-api",
            "full_name": "octo-org/quality-api",
            "owner": {"login": "octo-org"},
            "default_branch": "main",
            "permissions": {"admin": True, "pull": True},
        },
        {
            "id": 457,
            "name": "private-api",
            "full_name": "octo-org/private-api",
            "owner": {"login": "octo-org"},
            "default_branch": "main",
            "permissions": {"admin": True, "pull": True},
        },
    ]
    github_installation_service.sync_installation_payload(
        db_session,
        user=current_user,
        installation_payload=installation_payload,
        repositories_payload=repositories,
    )
    github_installation_service.sync_installation_payload(
        db_session,
        user=other_user,
        installation_payload=installation_payload,
        repositories_payload=repositories,
    )

    monkeypatch.setattr(
        github_installation_service.token_crypto_service,
        "decrypt_token",
        lambda value: "oauth-token",
    )

    def fake_resource(token, path, collection_key):
        assert token == "oauth-token"
        if path == "/user/installations":
            return [installation_payload]
        return [repositories[0]]

    monkeypatch.setattr(
        github_installation_service,
        "_get_paginated_user_resource",
        fake_resource,
    )

    github_installation_service.sync_user_installations(
        db_session,
        current_user,
    )

    assert db_session.query(InstallationRepository).count() == 2
    assert (
        db_session.query(UserRepositoryAccess)
        .filter_by(user_id=other_user.id)
        .count()
        == 2
    )
    current_access = (
        db_session.query(UserRepositoryAccess)
        .filter_by(user_id=current_user.id)
        .one()
    )
    assert current_access.repository.full_name == "octo-org/quality-api"


def test_suspend_preserves_installation_links_until_deletion(
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
        },
        repositories_payload=[
            {
                "id": 456,
                "name": "quality-api",
                "full_name": "octo-org/quality-api",
                "owner": {"login": "octo-org"},
                "permissions": {"admin": True},
            }
        ],
    )

    github_installation_service.deactivate_installation(
        db_session,
        installation.installation_id,
        suspended_at=installation.updated_at,
    )

    assert db_session.query(InstallationRepository).count() == 1
    assert db_session.query(UserRepositoryAccess).count() == 1

    github_installation_service.deactivate_installation(
        db_session,
        installation.installation_id,
        purge=True,
    )

    assert db_session.query(InstallationRepository).count() == 0
    assert db_session.query(UserRepositoryAccess).count() == 0
