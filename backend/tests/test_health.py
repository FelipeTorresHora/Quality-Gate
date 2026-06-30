def test_health_returns_ok(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_database_health_returns_ok(client):
    response = client.get("/health/db")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_readiness_returns_ok(client, monkeypatch):
    from app.api import routes_health

    class FakeResponse:
        is_error = False

    monkeypatch.setattr(
        routes_health.github_app_auth_service,
        "generate_app_jwt",
        lambda: "jwt",
    )
    monkeypatch.setattr(routes_health.httpx, "get", lambda *_, **__: FakeResponse())

    response = client.get("/health/readiness")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "database": "ok",
        "github_app": "ok",
    }
