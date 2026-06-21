def test_list_pull_requests_without_token_returns_structured_error(client, repository):
    response = client.get(f"/api/repositories/{repository['id']}/pull-requests")

    assert response.status_code == 503
    assert response.json()["detail"] == {
        "code": "github_token_missing",
        "message": "GitHub token is not configured.",
    }
