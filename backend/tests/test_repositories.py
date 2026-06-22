def test_create_repository_creates_default_quality_gate_config(client, reset_database):
    response = client.post(
        "/api/repositories",
        json={
            "owner": "horinha04",
            "name": "meu-projeto",
            "full_name": "horinha04/meu-projeto",
            "default_branch": "main",
        },
    )

    assert response.status_code == 201
    repository = response.json()
    assert repository["id"]
    assert repository["owner"] == "horinha04"
    assert repository["name"] == "meu-projeto"
    assert repository["full_name"] == "horinha04/meu-projeto"
    assert repository["default_branch"] == "main"
    assert "user_id" not in repository

    config_response = client.get(
        f"/api/repositories/{repository['id']}/quality-gate-config"
    )
    assert config_response.status_code == 200
    config = config_response.json()
    assert config["repository_id"] == repository["id"]
    assert config["min_total_coverage"] == 80
    assert config["max_coverage_drop"] == 0
    assert config["min_changed_files_coverage"] == 75
    assert config["security_fail_on"] == ["critical", "high"]
    assert config["max_function_lines"] == 80
    assert config["max_complexity"] == 10
    assert config["fail_on_new_todo"] is True
    assert config["comment_on_github"] is False
    assert config["publish_github_status"] is False


def test_list_repositories_returns_created_repository(client, repository):
    response = client.get("/api/repositories")

    assert response.status_code == 200
    repositories = response.json()
    assert len(repositories) == 1
    assert repositories[0]["id"] == repository["id"]
    assert repositories[0]["full_name"] == "horinha04/meu-projeto"


def test_create_repository_rejects_duplicate_full_name(client, repository):
    response = client.post(
        "/api/repositories",
        json={
            "owner": "horinha04",
            "name": "meu-projeto",
            "full_name": "horinha04/meu-projeto",
            "default_branch": "main",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "repository_already_exists"


def test_list_pull_requests_for_manual_repository_returns_empty_queue(client, repository):
    response = client.get(f"/api/repositories/{repository['id']}/pull-requests")

    assert response.status_code == 200
    assert response.json() == []


def test_list_pull_requests_includes_not_run_review_state(client, reset_database, monkeypatch):
    github_repository = _create_github_repository(client)
    _patch_pull_requests(monkeypatch, head_sha="abc123")

    response = client.get(f"/api/repositories/{github_repository['id']}/pull-requests")

    assert response.status_code == 200
    pull_requests = response.json()
    assert len(pull_requests) == 1
    assert pull_requests[0]["number"] == 42
    assert pull_requests[0]["review_state"] == {
        "state": "not_run",
        "analysis_run": None,
    }


def test_list_pull_requests_marks_matching_head_sha_as_current(
    client, reset_database, monkeypatch
):
    github_repository = _create_github_repository(client)
    _patch_pull_requests(monkeypatch, head_sha="abc123")
    created = client.post(
        f"/api/repositories/{github_repository['id']}/analysis-runs/mock",
        json={"scenario": "passing", "pr_number": 42, "head_sha": "abc123"},
    ).json()

    response = client.get(f"/api/repositories/{github_repository['id']}/pull-requests")

    assert response.status_code == 200
    review_state = response.json()[0]["review_state"]
    assert review_state["state"] == "current"
    assert review_state["analysis_run"] == {
        "id": created["id"],
        "status": "completed",
        "decision": "pass",
        "score": 96,
        "trigger_source": "mock",
        "head_sha": "abc123",
        "created_at": created["created_at"],
    }


def test_list_pull_requests_marks_different_head_sha_as_outdated(
    client, reset_database, monkeypatch
):
    github_repository = _create_github_repository(client)
    _patch_pull_requests(monkeypatch, head_sha="new-sha")
    created = client.post(
        f"/api/repositories/{github_repository['id']}/analysis-runs/mock",
        json={"scenario": "passing", "pr_number": 42, "head_sha": "old-sha"},
    ).json()

    response = client.get(f"/api/repositories/{github_repository['id']}/pull-requests")

    assert response.status_code == 200
    review_state = response.json()[0]["review_state"]
    assert review_state["state"] == "outdated"
    assert review_state["analysis_run"]["id"] == created["id"]
    assert review_state["analysis_run"]["head_sha"] == "old-sha"


def _create_github_repository(client):
    response = client.post(
        "/api/repositories",
        json={
            "owner": "horinha04",
            "name": "github-projeto",
            "full_name": "horinha04/github-projeto",
            "default_branch": "main",
            "github_repo_id": 123456,
        },
    )
    assert response.status_code == 201
    return response.json()


def _patch_pull_requests(monkeypatch, head_sha: str):
    from app.schemas.github import GitHubPullRequestRead
    from app.services.github_service import GitHubClient

    def fake_list_pull_requests(self, owner, name):
        assert (owner, name) == ("horinha04", "github-projeto")
        return [
            GitHubPullRequestRead(
                number=42,
                title="Add dashboard review state",
                user_login="octocat",
                state="open",
                draft=False,
                head_ref="feature/dashboard",
                head_sha=head_sha,
                base_ref="main",
                html_url="https://github.com/horinha04/github-projeto/pull/42",
                created_at="2026-06-21T10:00:00Z",
                updated_at="2026-06-21T11:00:00Z",
            )
        ]

    monkeypatch.setattr(
        GitHubClient, "list_pull_requests", fake_list_pull_requests, raising=False
    )
