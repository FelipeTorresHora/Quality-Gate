from app.core.errors import AppError
from app.services import github_app_auth_service


def test_list_pull_requests_with_installation_token_failure_returns_structured_error(
    client,
    repository,
    monkeypatch,
):
    monkeypatch.setattr(
        github_app_auth_service,
        "generate_installation_token",
        lambda installation_id: _raise_installation_token_error(),
    )

    response = client.get(
        f"/api/repositories/{repository['id']}/pull-requests"
    )

    assert response.status_code == 503
    assert response.json()["detail"] == {
        "code": "github_installation_token_failed",
        "message": "GitHub installation token could not be generated.",
    }


def _raise_installation_token_error():
    raise AppError(
        503,
        "github_installation_token_failed",
        "GitHub installation token could not be generated.",
    )
