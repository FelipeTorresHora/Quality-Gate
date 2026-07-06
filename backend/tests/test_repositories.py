from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import event

from app.db.session import SessionLocal
from app.models.analysis_run import AnalysisRun
from app.models.enums import AnalysisRunStatus, AnalysisTriggerSource, GateDecision


def test_manual_repository_creation_endpoint_is_removed(client, repository):
    response = client.post(
        "/api/repositories",
        json={"owner": "octo-org", "name": "quality-api", "default_branch": "main"},
    )

    assert response.status_code == 405


def test_github_repository_creation_endpoint_is_removed(client, repository):
    response = client.post(
        "/api/repositories/github",
        json={"owner": "octo-org", "name": "quality-api"},
    )

    assert response.status_code == 405


def test_list_repositories_returns_synced_repository(client, repository):
    response = client.get("/api/repositories")

    assert response.status_code == 200
    repositories = response.json()
    assert len(repositories) == 1
    assert repositories[0]["id"] == repository["id"]
    assert repositories[0]["full_name"] == "horinha04/meu-projeto"


def test_list_repositories_cache_miss_uses_user_scoped_key(
    client, repository, monkeypatch
):
    writes = []
    monkeypatch.setattr(
        "app.api.routes_repositories.runtime_cache_service.get_json",
        lambda key: None,
    )
    monkeypatch.setattr(
        "app.api.routes_repositories.runtime_cache_service.set_json",
        lambda key, value, ttl, tags: writes.append(
            {"key": key, "value": value, "ttl": ttl, "tags": tags}
        ),
    )

    response = client.get("/api/repositories")

    assert response.status_code == 200
    assert writes
    assert writes[0]["key"].startswith("repositories:v1:user:")
    assert writes[0]["ttl"] == 120
    assert "repositories" in writes[0]["tags"]


def test_get_repository_cache_hit_still_requires_access(
    client, repository, monkeypatch
):
    cache_reads = []
    monkeypatch.setattr(
        "app.api.routes_repositories.runtime_cache_service.get_json",
        lambda key: cache_reads.append(key) or {"id": repository["id"]},
    )

    response = client.get(
        "/api/repositories/00000000-0000-0000-0000-000000000000"
    )

    assert response.status_code == 403
    assert cache_reads == []


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


def test_list_pull_requests_cache_hit_still_requires_access(
    client, repository, monkeypatch
):
    cache_reads = []
    monkeypatch.setattr(
        "app.api.routes_repositories.runtime_cache_service.get_json",
        lambda key: cache_reads.append(key) or [],
    )

    response = client.get(
        "/api/repositories/00000000-0000-0000-0000-000000000000/pull-requests"
    )

    assert response.status_code == 403
    assert cache_reads == []


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


def test_list_pull_requests_batches_review_state_for_multiple_prs(
    client,
    repository,
    monkeypatch,
):
    _patch_pull_requests(
        monkeypatch,
        pull_requests=[
            _pull_request(number=1, head_sha="sha-current"),
            _pull_request(number=2, head_sha="sha-new"),
            _pull_request(number=3, head_sha="sha-missing"),
        ],
    )
    _insert_analysis_run(repository["id"], pr_number=1, head_sha="sha-current")
    _insert_analysis_run(repository["id"], pr_number=2, head_sha="sha-old")

    def fail_single_item_review_state(*args, **kwargs):
        raise AssertionError("single-item review state should not be used for PR lists")

    monkeypatch.setattr(
        "app.services.pull_request_review_service.get_pull_request_review_state",
        fail_single_item_review_state,
    )

    response = client.get(f"/api/repositories/{repository['id']}/pull-requests")

    assert response.status_code == 200
    pull_requests = {item["number"]: item for item in response.json()}
    assert pull_requests[1]["review_state"]["state"] == "current"
    assert pull_requests[2]["review_state"]["state"] == "outdated"
    assert pull_requests[3]["review_state"] == {
        "state": "not_run",
        "analysis_run": None,
    }


def test_list_pull_requests_uses_latest_run_per_pr(
    client,
    repository,
    monkeypatch,
):
    _patch_pull_requests(
        monkeypatch,
        pull_requests=[
            _pull_request(number=7, head_sha="sha-current"),
        ],
    )
    _insert_analysis_run(
        repository["id"],
        pr_number=7,
        head_sha="sha-old",
        created_at=datetime(2026, 6, 21, 10, 0, tzinfo=UTC),
    )
    latest = _insert_analysis_run(
        repository["id"],
        pr_number=7,
        head_sha="sha-current",
        created_at=datetime(2026, 6, 21, 11, 0, tzinfo=UTC),
    )

    response = client.get(f"/api/repositories/{repository['id']}/pull-requests")

    assert response.status_code == 200
    review_state = response.json()[0]["review_state"]
    assert review_state["state"] == "current"
    assert review_state["analysis_run"]["id"] == latest["id"]
    assert review_state["analysis_run"]["head_sha"] == "sha-current"


def test_pull_request_review_state_batch_queries_analysis_runs_once(
    db_session,
    repository,
):
    from app.services.pull_request_review_service import get_pull_request_review_states

    _insert_analysis_run(repository["id"], pr_number=1, head_sha="sha-1")
    _insert_analysis_run(repository["id"], pr_number=2, head_sha="sha-2")
    pull_requests = [
        _pull_request(number=1, head_sha="sha-1"),
        _pull_request(number=2, head_sha="sha-new"),
        _pull_request(number=3, head_sha="sha-missing"),
    ]
    analysis_run_queries = []

    def count_analysis_run_queries(
        conn, cursor, statement, parameters, context, executemany
    ):
        if "FROM analysis_runs" in statement:
            analysis_run_queries.append(statement)

    event.listen(db_session.bind, "before_cursor_execute", count_analysis_run_queries)
    try:
        states = get_pull_request_review_states(
            db_session, UUID(repository["id"]), pull_requests
        )
    finally:
        event.remove(
            db_session.bind, "before_cursor_execute", count_analysis_run_queries
        )

    assert len(analysis_run_queries) == 1
    assert states[1].state == "current"
    assert states[2].state == "outdated"
    assert states[3].state == "not_run"


def _insert_analysis_run(
    repository_id: str,
    *,
    head_sha: str,
    pr_number: int = 42,
    created_at: datetime | None = None,
) -> dict[str, str]:
    with SessionLocal() as db:
        run = AnalysisRun(
            repository_id=UUID(repository_id),
            pr_number=pr_number,
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
        if created_at is not None:
            run.created_at = created_at
        db.add(run)
        db.commit()
        return {
            "id": str(run.id),
            "created_at": run.created_at.isoformat().replace("+00:00", "Z"),
        }


def _pull_request(number: int, head_sha: str):
    from app.schemas.github import GitHubPullRequestRead

    return GitHubPullRequestRead(
        number=number,
        title="Add dashboard review state",
        user_login="octocat",
        state="open",
        draft=False,
        head_ref="feature/dashboard",
        head_sha=head_sha,
        base_ref="main",
        html_url=f"https://github.com/horinha04/meu-projeto/pull/{number}",
        created_at="2026-06-21T10:00:00Z",
        updated_at="2026-06-21T11:00:00Z",
    )


def _patch_pull_requests(monkeypatch, head_sha: str = "abc123", pull_requests=None):
    from app.services.github_service import GitHubClient

    def fake_list_pull_requests(self, owner, name):
        assert (owner, name) == ("horinha04", "meu-projeto")
        return pull_requests or [_pull_request(number=42, head_sha=head_sha)]

    monkeypatch.setattr(
        GitHubClient,
        "list_pull_requests",
        fake_list_pull_requests,
        raising=False,
    )
