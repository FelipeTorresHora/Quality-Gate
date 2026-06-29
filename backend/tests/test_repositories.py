from uuid import UUID

from app.db.session import SessionLocal
from app.models.analysis_run import AnalysisRun
from app.models.enums import AnalysisRunStatus, AnalysisTriggerSource, GateDecision


def test_manual_repository_creation_endpoint_is_removed(client, repository):
    response = client.post(
        "/api/repositories",
        json={"owner": "octo-org", "name": "quality-api", "default_branch": "main"},
    )

    assert response.status_code == 404


def test_github_repository_creation_endpoint_is_removed(client, repository):
    response = client.post(
        "/api/repositories/github",
        json={"owner": "octo-org", "name": "quality-api"},
    )

    assert response.status_code == 404


def test_list_repositories_returns_synced_repository(client, repository):
    response = client.get("/api/repositories")

    assert response.status_code == 200
    repositories = response.json()
    assert len(repositories) == 1
    assert repositories[0]["id"] == repository["id"]
    assert repositories[0]["full_name"] == "horinha04/meu-projeto"


def test_list_pull_requests_includes_not_run_review_state(
    client,
    repository,
    monkeypatch,
):
    _patch_pull_requests(monkeypatch, head_sha="abc123")

    response = client.get(f"/api/repositories/{repository['id']}/pull-requests")

    assert response.status_code == 200
    pull_requests = response.json()
    assert len(pull_requests) == 1
    assert pull_requests[0]["number"] == 42
    assert pull_requests[0]["review_state"] == {
        "state": "not_run",
        "analysis_run": None,
    }


def test_list_pull_requests_marks_matching_head_sha_as_current(
    client,
    repository,
    monkeypatch,
):
    _patch_pull_requests(monkeypatch, head_sha="abc123")
    created = _insert_analysis_run(repository["id"], head_sha="abc123")

    response = client.get(f"/api/repositories/{repository['id']}/pull-requests")

    assert response.status_code == 200
    review_state = response.json()[0]["review_state"]
    assert review_state["state"] == "current"
    assert review_state["analysis_run"] == {
        "id": created["id"],
        "status": "completed",
        "decision": "pass",
        "score": 96.0,
        "trigger_source": "manual",
        "head_sha": "abc123",
        "created_at": created["created_at"],
    }


def test_list_pull_requests_marks_different_head_sha_as_outdated(
    client,
    repository,
    monkeypatch,
):
    _patch_pull_requests(monkeypatch, head_sha="new-sha")
    created = _insert_analysis_run(repository["id"], head_sha="old-sha")

    response = client.get(f"/api/repositories/{repository['id']}/pull-requests")

    assert response.status_code == 200
    review_state = response.json()[0]["review_state"]
    assert review_state["state"] == "outdated"
    assert review_state["analysis_run"]["id"] == created["id"]
    assert review_state["analysis_run"]["head_sha"] == "old-sha"


def _insert_analysis_run(repository_id: str, *, head_sha: str) -> dict[str, str]:
    with SessionLocal() as db:
        run = AnalysisRun(
            repository_id=UUID(repository_id),
            pr_number=42,
            head_sha=head_sha,
            status=AnalysisRunStatus.COMPLETED,
            decision=GateDecision.PASS,
            trigger_source=AnalysisTriggerSource.MANUAL,
            score=96,
            coverage_result_json={"status": "pass"},
            security_result_json={"status": "pass"},
            technical_debt_result_json={"status": "pass"},
            ai_review_json={},
            pull_request_snapshot_json={"number": 42},
            changed_files_snapshot_json=[],
            diff_truncated=False,
        )
        db.add(run)
        db.commit()
        return {
            "id": str(run.id),
            "created_at": run.created_at.isoformat().replace("+00:00", "Z"),
        }


def _patch_pull_requests(monkeypatch, head_sha: str):
    from app.schemas.github import GitHubPullRequestRead
    from app.services.github_service import GitHubClient

    def fake_list_pull_requests(self, owner, name):
        assert (owner, name) == ("horinha04", "meu-projeto")
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
                html_url="https://github.com/horinha04/meu-projeto/pull/42",
                created_at="2026-06-21T10:00:00Z",
                updated_at="2026-06-21T11:00:00Z",
            )
        ]

    monkeypatch.setattr(
        GitHubClient,
        "list_pull_requests",
        fake_list_pull_requests,
        raising=False,
    )
