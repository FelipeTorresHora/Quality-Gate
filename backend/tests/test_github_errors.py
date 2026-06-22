def test_list_pull_requests_without_token_returns_structured_error(
    client, reset_database
):
    repository_response = client.post(
        "/api/repositories",
        json={
            "owner": "horinha04",
            "name": "github-projeto",
            "full_name": "horinha04/github-projeto",
            "default_branch": "main",
            "github_repo_id": 123456,
        },
    )
    assert repository_response.status_code == 201

    response = client.get(
        f"/api/repositories/{repository_response.json()['id']}/pull-requests"
    )

    assert response.status_code == 503
    assert response.json()["detail"] == {
        "code": "github_token_missing",
        "message": "GitHub token is not configured.",
    }
