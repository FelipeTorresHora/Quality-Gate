from datetime import UTC, datetime, timedelta

import pytest

from app.services import github_app_auth_service


def test_generate_app_jwt_requires_private_key(monkeypatch):
    monkeypatch.setenv("GITHUB_APP_ID", "123")
    monkeypatch.delenv("GITHUB_APP_PRIVATE_KEY", raising=False)
    monkeypatch.delenv("GITHUB_APP_PRIVATE_KEY_PATH", raising=False)
    github_app_auth_service.get_settings.cache_clear()

    with pytest.raises(Exception) as exc:
        github_app_auth_service.generate_app_jwt()

    assert "github_app_private_key" in str(exc.value)


def test_installation_token_is_not_persisted(monkeypatch):
    calls = []

    class FakeResponse:
        status_code = 201
        headers = {}

        def json(self):
            return {
                "token": "installation-token",
                "expires_at": (
                    datetime.now(UTC) + timedelta(hours=1)
                ).isoformat(),
            }

        @property
        def is_error(self):
            return False

    def fake_post(url, headers, timeout):
        calls.append((url, headers))
        return FakeResponse()

    monkeypatch.setattr(github_app_auth_service.httpx, "post", fake_post)
    monkeypatch.setattr(
        github_app_auth_service,
        "generate_app_jwt",
        lambda: "jwt-token",
    )

    token = github_app_auth_service.generate_installation_token(42)

    assert token == "installation-token"
    assert calls[0][0].endswith("/app/installations/42/access_tokens")
    assert calls[0][1]["Authorization"] == "Bearer jwt-token"
