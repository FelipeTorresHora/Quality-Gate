from datetime import UTC, datetime, timedelta

import jwt
import pytest
from fastapi import Response

from app.core.config import Settings, validate_runtime_security_settings
from app.core.errors import AppError
from app.models.github_app_installation import GitHubAppInstallation
from app.models.installation_repository import InstallationRepository
from app.models.repository import Repository
from app.models.user import User
from app.models.user_repository_access import UserRepositoryAccess
from app.models.user_session import UserSession
from app.services import github_oauth_service, session_service, token_crypto_service


def test_production_rejects_default_session_secret():
    settings = Settings(
        app_env="production",
        session_secret="change-me",
        token_encryption_key="valid-token-key",
    )

    with pytest.raises(RuntimeError, match="SESSION_SECRET"):
        validate_runtime_security_settings(settings)


def test_oauth_state_expires(reset_database, db_session):
    created = github_oauth_service.create_oauth_state(
        db_session, ttl=timedelta(seconds=-1)
    )

    with pytest.raises(AppError) as exc:
        github_oauth_service.consume_oauth_state(db_session, created.state)

    assert exc.value.code == "github_oauth_state_invalid"


def test_oauth_state_is_single_use(reset_database, db_session):
    created = github_oauth_service.create_oauth_state(
        db_session, ttl=timedelta(minutes=10)
    )

    github_oauth_service.consume_oauth_state(db_session, created.state)

    with pytest.raises(AppError) as exc:
        github_oauth_service.consume_oauth_state(db_session, created.state)

    assert exc.value.code == "github_oauth_state_invalid"


def test_cookie_policy_helper_sets_secure_flags(monkeypatch):
    monkeypatch.setenv("SESSION_COOKIE_SECURE", "true")
    session_service.get_settings.cache_clear()
    response = Response()
    created = session_service.CreatedSession(
        cookie_value="session-cookie",
        csrf_token="csrf-token",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
    )

    session_service.set_session_cookies(response, created)

    set_cookie_headers = [
        value.decode("latin-1")
        for key, value in response.raw_headers
        if key == b"set-cookie"
    ]
    session_cookie = next(
        header for header in set_cookie_headers if header.startswith("qg_session=")
    )
    csrf_cookie = next(
        header for header in set_cookie_headers if header.startswith("qg_csrf=")
    )
    assert "HttpOnly" in session_cookie
    assert "Secure" in session_cookie
    assert "SameSite=lax" in session_cookie
    assert "HttpOnly" not in csrf_cookie
    assert "Secure" in csrf_cookie
    session_service.get_settings.cache_clear()


def test_user_session_and_repository_access_models_persist(reset_database, db_session):
    user = User(
        github_user_id=123,
        github_login="octocat",
        name="Octo Cat",
        email=None,
        avatar_url="https://avatars.githubusercontent.com/u/123",
    )
    repository = Repository(
        github_repo_id=456,
        owner="octo-org",
        name="quality-api",
        full_name="octo-org/quality-api",
        default_branch="main",
    )
    installation = GitHubAppInstallation(
        installation_id=789,
        account_id=321,
        account_login="octo-org",
        account_type="Organization",
        repository_selection="selected",
        permissions_json={"contents": "read", "pull_requests": "read"},
        events_json=["pull_request"],
        active=True,
    )
    db_session.add_all([user, repository, installation])
    db_session.flush()
    db_session.add(
        InstallationRepository(
            installation_id=installation.id,
            repository_id=repository.id,
            github_repo_id=456,
            full_name="octo-org/quality-api",
        )
    )
    db_session.add(
        UserRepositoryAccess(
            user_id=user.id,
            repository_id=repository.id,
            installation_id=installation.id,
            permission="admin",
            is_admin=True,
            synced_at=datetime.now(UTC),
        )
    )
    db_session.add(
        UserSession(
            user_id=user.id,
            session_token_hash="session-hash",
            csrf_token_hash="csrf-hash",
            expires_at=datetime.now(UTC) + timedelta(hours=8),
        )
    )
    db_session.commit()

    persisted_installation = db_session.query(GitHubAppInstallation).one()
    persisted_installation_repository = db_session.query(InstallationRepository).one()

    assert persisted_installation.installation_id == 789
    assert persisted_installation.account_login == "octo-org"
    assert persisted_installation.permissions_json == {
        "contents": "read",
        "pull_requests": "read",
    }
    assert persisted_installation_repository.installation_id == persisted_installation.id
    assert persisted_installation_repository.repository_id == repository.id
    assert persisted_installation_repository.full_name == "octo-org/quality-api"
    assert db_session.query(UserSession).count() == 1
    assert db_session.query(UserRepositoryAccess).one().is_admin is True


def test_create_session_returns_raw_cookie_once(reset_database, db_session):
    user = User(github_user_id=1, github_login="octocat")
    db_session.add(user)
    db_session.commit()

    created = session_service.create_session(
        db_session, user, ttl=timedelta(hours=1)
    )

    assert created.cookie_value
    assert created.csrf_token
    assert created.expires_at > datetime.now(UTC)
    assert db_session.query(UserSession).count() == 1
    current_user = session_service.get_user_for_session(
        created.cookie_value, db_session
    )
    assert current_user.id == user.id
    assert current_user.github_user_id == 1
    assert current_user.github_login == "octocat"
    assert current_user.has_github_connection is False


def test_revoke_session_invalidates_stored_session(reset_database, db_session):
    user = User(github_user_id=1, github_login="octocat")
    db_session.add(user)
    db_session.commit()
    created = session_service.create_session(
        db_session, user, ttl=timedelta(hours=1)
    )

    session_service.revoke_session(db_session, created.cookie_value)

    assert session_service.get_user_for_session(
        created.cookie_value, db_session
    ) is None


def test_expired_session_is_rejected(reset_database, db_session):
    user = User(github_user_id=1, github_login="octocat")
    db_session.add(user)
    db_session.commit()
    created = session_service.create_session(
        db_session, user, ttl=timedelta(seconds=-1)
    )

    assert session_service.get_user_for_session(created.cookie_value) is None


def test_tampered_session_cookie_is_rejected(reset_database, db_session):
    user = User(github_user_id=1, github_login="octocat")
    db_session.add(user)
    db_session.commit()
    created = session_service.create_session(db_session, user)

    header, payload, signature = created.cookie_value.split(".")
    tampered_signature = (
        ("a" if signature[0] != "a" else "b") + signature[1:]
    )
    tampered = ".".join([header, payload, tampered_signature])

    assert session_service.get_user_for_session(tampered) is None


def test_csrf_token_validates_against_session_claim(reset_database, db_session):
    user = User(github_user_id=1, github_login="octocat")
    db_session.add(user)
    db_session.commit()
    created = session_service.create_session(db_session, user)

    assert session_service.validate_csrf_token(
        created.cookie_value, created.csrf_token
    )
    assert not session_service.validate_csrf_token(created.cookie_value, "wrong")


def test_session_cookie_does_not_expose_csrf_token(reset_database, db_session):
    user = User(github_user_id=1, github_login="octocat")
    db_session.add(user)
    db_session.commit()
    created = session_service.create_session(db_session, user)

    payload = jwt.decode(
        created.cookie_value,
        options={"verify_signature": False},
        algorithms=["HS256"],
    )

    assert payload["csrf_hash"] != created.csrf_token
    assert "csrf_token" not in payload


def test_me_requires_authentication(client):
    response = client.get("/api/auth/me")

    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "authentication_required"


def test_logout_revokes_session_when_store_enabled(client, db_session):
    user = User(github_user_id=1, github_login="octocat")
    db_session.add(user)
    db_session.commit()
    created = session_service.create_session(db_session, user)
    client.cookies.set("qg_session", created.cookie_value)
    client.cookies.set("qg_csrf", created.csrf_token)

    response = client.post(
        "/api/auth/logout",
        headers={"X-CSRF-Token": created.csrf_token},
    )

    assert response.status_code == 200
    assert db_session.query(UserSession).one().revoked_at is not None
    assert session_service.get_user_for_session(
        created.cookie_value, db_session
    ) is None


def test_logout_rejects_missing_stateless_csrf(client, db_session):
    user = User(github_user_id=1, github_login="octocat")
    db_session.add(user)
    db_session.commit()
    created = session_service.create_session(db_session, user)
    client.cookies.set("qg_session", created.cookie_value)
    client.cookies.set("qg_csrf", created.csrf_token)

    response = client.post("/api/auth/logout")

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "csrf_token_invalid"


def test_login_redirects_to_github(monkeypatch, client, reset_database):
    monkeypatch.setenv("GITHUB_APP_CLIENT_ID", "client-id")
    monkeypatch.setenv(
        "AUTH_CALLBACK_URL",
        "http://localhost:8000/api/auth/github/callback",
    )
    from app.services import github_oauth_service

    github_oauth_service.get_settings.cache_clear()

    response = client.get("/api/auth/github/login", follow_redirects=False)

    assert response.status_code in {302, 307}
    assert "github.com/login/oauth/authorize" in response.headers["location"]
    assert "client_id=client-id" in response.headers["location"]
    github_oauth_service.get_settings.cache_clear()


def test_token_crypto_round_trip(monkeypatch):
    key = token_crypto_service.generate_key()
    monkeypatch.setenv("TOKEN_ENCRYPTION_KEY", key)
    token_crypto_service.get_settings.cache_clear()

    encrypted = token_crypto_service.encrypt_token("secret-token")

    assert encrypted != "secret-token"
    assert token_crypto_service.decrypt_token(encrypted) == "secret-token"
    token_crypto_service.get_settings.cache_clear()
