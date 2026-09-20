import pytest

from app.core.errors import AppError
from app.models.user import User
from app.services import github_oauth_service, token_crypto_service


def test_build_login_url_requires_client_id(monkeypatch, reset_database, db_session):
    monkeypatch.delenv("GITHUB_APP_CLIENT_ID", raising=False)
    github_oauth_service.get_settings.cache_clear()
    with pytest.raises(AppError) as exc:
        github_oauth_service.build_login_url(db_session)
    assert exc.value.code == "github_app_config_missing"
    github_oauth_service.get_settings.cache_clear()


def test_exchange_code_for_user_success(monkeypatch, reset_database, db_session):
    created = github_oauth_service.create_oauth_state(db_session)
    monkeypatch.setenv("GITHUB_APP_CLIENT_ID", "client")
    monkeypatch.setenv("GITHUB_APP_CLIENT_SECRET", "secret")
    monkeypatch.setenv("AUTH_CALLBACK_URL", "http://localhost/callback")
    github_oauth_service.get_settings.cache_clear()

    class TokenResponse:
        is_error = False

        def json(self):
            return {"access_token": "gho_token"}

    class UserResponse:
        is_error = False

        def json(self):
            return {
                "id": 99,
                "login": "new-user",
                "name": "New",
                "email": "n@example.com",
                "avatar_url": "https://example.com/a.png",
            }

    calls = []

    def fake_post(url, **kwargs):
        calls.append(("post", url))
        return TokenResponse()

    def fake_get(url, **kwargs):
        calls.append(("get", url))
        return UserResponse()

    monkeypatch.setattr(github_oauth_service.httpx, "post", fake_post)
    monkeypatch.setattr(github_oauth_service.httpx, "get", fake_get)
    monkeypatch.setattr(
        github_oauth_service.github_installation_service,
        "sync_user_installations",
        lambda db, user: None,
    )
    key = token_crypto_service.generate_key()
    monkeypatch.setenv("TOKEN_ENCRYPTION_KEY", key)
    token_crypto_service.get_settings.cache_clear()

    user = github_oauth_service.exchange_code_for_user(
        "auth-code", created.state, db_session
    )

    assert user.github_login == "new-user"
    assert calls[0][0] == "post"
    assert calls[1][0] == "get"
    token_crypto_service.get_settings.cache_clear()
    github_oauth_service.get_settings.cache_clear()


def test_exchange_code_for_user_handles_token_errors(monkeypatch, reset_database, db_session):
    created = github_oauth_service.create_oauth_state(db_session)
    monkeypatch.setenv("GITHUB_APP_CLIENT_ID", "client")
    monkeypatch.setenv("GITHUB_APP_CLIENT_SECRET", "secret")
    github_oauth_service.get_settings.cache_clear()

    class ErrorResponse:
        is_error = True

        def json(self):
            return {}

    monkeypatch.setattr(
        github_oauth_service.httpx, "post", lambda *args, **kwargs: ErrorResponse()
    )
    with pytest.raises(AppError) as exc:
        github_oauth_service.exchange_code_for_user("code", created.state, db_session)
    assert exc.value.code == "github_oauth_exchange_failed"
    github_oauth_service.get_settings.cache_clear()


def test_exchange_code_for_user_missing_access_token(monkeypatch, reset_database, db_session):
    created = github_oauth_service.create_oauth_state(db_session)
    monkeypatch.setenv("GITHUB_APP_CLIENT_ID", "client")
    monkeypatch.setenv("GITHUB_APP_CLIENT_SECRET", "secret")
    github_oauth_service.get_settings.cache_clear()

    class TokenResponse:
        is_error = False

        def json(self):
            return {}

    monkeypatch.setattr(
        github_oauth_service.httpx, "post", lambda *args, **kwargs: TokenResponse()
    )
    with pytest.raises(AppError) as exc:
        github_oauth_service.exchange_code_for_user("code", created.state, db_session)
    assert exc.value.code == "github_oauth_exchange_failed"
    github_oauth_service.get_settings.cache_clear()


def test_upsert_user_updates_existing_connection(reset_database, db_session, monkeypatch):
    user = User(github_user_id=5, github_login="old")
    db_session.add(user)
    db_session.commit()
    key = token_crypto_service.generate_key()
    monkeypatch.setenv("TOKEN_ENCRYPTION_KEY", key)
    token_crypto_service.get_settings.cache_clear()

    updated = github_oauth_service.upsert_user_from_github(
        db_session,
        {"id": 5, "login": "new-login", "name": "Name"},
        "token-value",
    )
    assert updated.github_login == "new-login"
    assert len(updated.github_connections) == 1
    token_crypto_service.get_settings.cache_clear()
