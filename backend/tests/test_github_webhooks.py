import hashlib
import hmac
import json
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.core.config import get_settings
from app.core.errors import AppError
from app.models.enums import AnalysisRunStatus
from app.services import github_webhook_service


WEBHOOK_SECRET = "test-webhook-secret"
ENRICHMENT_ERROR = (
    "GitHub Pull Request context could not be captured. "
    "Check token permissions and try again with a new Pull Request event."
)


@pytest.fixture
def webhook_secret(monkeypatch):
    monkeypatch.setenv("GITHUB_WEBHOOK_SECRET", WEBHOOK_SECRET)
    get_settings.cache_clear()
    yield WEBHOOK_SECRET
    get_settings.cache_clear()


def _signed_headers(body: bytes, event: str = "pull_request") -> dict[str, str]:
    signature = hmac.new(
        WEBHOOK_SECRET.encode(), body, hashlib.sha256
    ).hexdigest()
    return {
        "Content-Type": "application/json",
        "X-GitHub-Event": event,
        "X-Hub-Signature-256": f"sha256={signature}",
    }


def _post_webhook(client, payload: dict, event: str = "pull_request"):
    body = json.dumps(payload, separators=(",", ":")).encode()
    return client.post(
        "/api/github/webhooks",
        content=body,
        headers=_signed_headers(body, event=event),
    )


def _pull_request_payload(
    *,
    action: str = "opened",
    draft: bool = False,
    state: str = "open",
    full_name: str = "horinha04/meu-projeto",
    number: int = 42,
    head_sha: str = "abc123",
):
    owner, name = full_name.split("/", 1)
    return {
        "action": action,
        "repository": {
            "full_name": full_name,
            "owner": {"login": owner},
            "name": name,
        },
        "pull_request": {
            "number": number,
            "title": "Add billing webhook",
            "body": "Implements billing webhook handling.",
            "state": state,
            "draft": draft,
            "user": {"login": "octocat"},
            "html_url": f"https://github.com/{full_name}/pull/{number}",
            "base": {"ref": "main", "sha": "base123"},
            "head": {"ref": "feature/billing-webhook", "sha": head_sha},
            "created_at": "2026-06-21T10:00:00Z",
            "updated_at": "2026-06-21T11:00:00Z",
        },
    }


def _pull_request_context(head_sha: str = "abc123", number: int = 42):
    return {
        "pull_request": {
            "number": number,
            "title": "Add billing webhook",
            "body": "Implements billing webhook handling.",
            "state": "open",
            "draft": False,
            "author_login": "octocat",
            "html_url": f"https://github.com/horinha04/meu-projeto/pull/{number}",
            "base_ref": "main",
            "head_ref": "feature/billing-webhook",
            "head_sha": head_sha,
            "base_sha": "base123",
            "created_at": "2026-06-21T10:00:00Z",
            "updated_at": "2026-06-21T11:00:00Z",
        },
        "changed_files": [
            {
                "filename": "backend/app/api/billing.py",
                "status": "added",
                "additions": 30,
                "deletions": 0,
                "changes": 30,
                "patch": "@@ -0,0 +1,30 @@",
            }
        ],
        "diff_snapshot": "diff --git a/backend/app/api/billing.py b/backend/app/api/billing.py\n",
        "diff_truncated": False,
    }


def _patch_context(monkeypatch, *, head_sha: str = "abc123"):
    from app.services.github_service import GitHubClient

    def fake_context(self, owner, name, pr_number):
        assert (owner, name, pr_number) == ("horinha04", "meu-projeto", 42)
        return _pull_request_context(head_sha=head_sha, number=pr_number)

    monkeypatch.setattr(
        GitHubClient, "get_pull_request_context", fake_context, raising=False
    )


def test_webhook_requires_configured_secret(client, monkeypatch):
    monkeypatch.setenv("GITHUB_WEBHOOK_SECRET", "")
    get_settings.cache_clear()
    payload = _pull_request_payload()
    body = json.dumps(payload, separators=(",", ":")).encode()

    response = client.post(
        "/api/github/webhooks",
        content=body,
        headers=_signed_headers(body),
    )

    assert response.status_code == 503
    assert response.json()["detail"] == {
        "code": "github_webhook_secret_missing",
        "message": "GitHub webhook secret is not configured.",
    }
    get_settings.cache_clear()


@pytest.mark.parametrize(
    "signature_header",
    [None, "sha256=invalid"],
)
def test_webhook_rejects_missing_or_invalid_signature(
    client, webhook_secret, signature_header
):
    payload = _pull_request_payload()
    body = json.dumps(payload, separators=(",", ":")).encode()
    headers = {"Content-Type": "application/json", "X-GitHub-Event": "pull_request"}
    if signature_header is not None:
        headers["X-Hub-Signature-256"] = signature_header

    response = client.post("/api/github/webhooks", content=body, headers=headers)

    assert response.status_code == 401
    assert response.json()["detail"] == {
        "code": "github_webhook_signature_invalid",
        "message": "GitHub webhook signature is invalid.",
    }


def test_webhook_ignores_unsupported_event(client, webhook_secret):
    response = _post_webhook(client, _pull_request_payload(), event="push")

    assert response.status_code == 202
    assert response.json() == {
        "status": "accepted",
        "ignored": True,
        "reason": "unsupported_event",
        "analysis_run_id": None,
    }


@pytest.mark.parametrize(
    ("payload", "reason"),
    [
        (_pull_request_payload(action="edited"), "unsupported_action"),
        (_pull_request_payload(action="closed", state="closed"), "closed_pull_request"),
        (_pull_request_payload(action="opened", draft=True), "draft_pull_request"),
        (_pull_request_payload(action="synchronize", draft=True), "draft_pull_request"),
        (
            _pull_request_payload(full_name="horinha04/unknown-repo"),
            "unknown_repository",
        ),
    ],
)
def test_webhook_ignores_relevant_non_triggering_cases(
    client, repository, webhook_secret, payload, reason
):
    response = _post_webhook(client, payload)

    assert response.status_code == 202
    assert response.json() == {
        "status": "accepted",
        "ignored": True,
        "reason": reason,
        "analysis_run_id": None,
    }


@pytest.mark.parametrize("action", ["opened", "reopened", "synchronize", "ready_for_review"])
def test_pull_request_webhook_creates_pending_analysis_run(
    client, repository, webhook_secret, monkeypatch, action
):
    _patch_context(monkeypatch)
    monkeypatch.setattr(
        "app.services.analysis_execution_service.execute_analysis_run",
        lambda db, analysis_run_id: None,
    )

    response = _post_webhook(client, _pull_request_payload(action=action))

    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "accepted"
    assert body["ignored"] is False
    assert body["reason"] is None
    assert body["analysis_run_id"]

    run_response = client.get(f"/api/analysis-runs/{body['analysis_run_id']}")
    assert run_response.status_code == 200
    run = run_response.json()
    assert run["repository_id"] == repository["id"]
    assert run["pr_number"] == 42
    assert run["head_sha"] == "abc123"
    assert run["status"] == "pending"
    assert run["decision"] is None
    assert run["score"] is None
    assert run["trigger_source"] == "github_webhook"
    assert run["pull_request_snapshot_json"]["title"] == "Add billing webhook"
    assert run["changed_files_snapshot_json"][0]["filename"].endswith("billing.py")
    assert run["diff_truncated"] is False
    assert "diff_snapshot" not in run


def test_pull_request_webhook_schedules_analysis_execution(
    monkeypatch, client, repository
):
    executed = []

    monkeypatch.setenv("GITHUB_WEBHOOK_SECRET", "secret")
    get_settings.cache_clear()
    monkeypatch.setattr(
        "app.services.github_webhook_service._has_valid_signature",
        lambda body, secret, signature_header: True,
    )
    monkeypatch.setattr(
        "app.services.github_service.GitHubClient.get_pull_request_context",
        lambda self, owner, name, pr_number: {
            "pull_request": {
                "number": pr_number,
                "title": "Improve quality",
                "body": None,
                "state": "open",
                "draft": False,
                "author_login": "octocat",
                "html_url": "https://github.com/horinha04/meu-projeto/pull/1",
                "base_ref": "main",
                "head_ref": "feature",
                "head_sha": "head-sha",
                "base_sha": "base-sha",
                "created_at": "2026-06-23T00:00:00Z",
                "updated_at": "2026-06-23T00:00:00Z",
            },
            "changed_files": [],
            "diff_snapshot": "diff --git a/a.py b/a.py",
            "diff_truncated": False,
        },
    )
    monkeypatch.setattr(
        "app.services.analysis_execution_service.execute_analysis_run",
        lambda db, analysis_run_id: executed.append(str(analysis_run_id)),
    )

    response = client.post(
        "/api/github/webhooks",
        headers={
            "X-GitHub-Event": "pull_request",
            "X-Hub-Signature-256": "sha256=test",
        },
        json={
            "action": "opened",
            "installation": {"id": 99},
            "repository": {"full_name": repository["full_name"]},
            "pull_request": {
                "number": 1,
                "title": "Improve quality",
                "body": None,
                "state": "open",
                "draft": False,
                "html_url": "https://github.com/horinha04/meu-projeto/pull/1",
                "user": {"login": "octocat"},
                "base": {"ref": "main", "sha": "base-sha"},
                "head": {"ref": "feature", "sha": "head-sha"},
                "created_at": "2026-06-23T00:00:00Z",
                "updated_at": "2026-06-23T00:00:00Z",
            },
        },
    )

    assert response.status_code == 202
    assert response.json()["analysis_run_id"] is not None
    assert executed
    get_settings.cache_clear()


def test_webhook_service_schedules_new_pending_run_without_database(monkeypatch):
    repository_id = uuid4()
    analysis_run_id = uuid4()
    scheduled = []
    payload = _pull_request_payload()
    body = json.dumps(payload).encode()

    monkeypatch.setenv("GITHUB_WEBHOOK_SECRET", "secret")
    get_settings.cache_clear()
    monkeypatch.setattr(
        github_webhook_service,
        "_has_valid_signature",
        lambda body, secret, signature_header: True,
    )
    monkeypatch.setattr(
        github_webhook_service,
        "get_repository_by_full_name",
        lambda db, full_name: SimpleNamespace(
            id=repository_id,
            owner="horinha04",
            name="meu-projeto",
        ),
    )
    monkeypatch.setattr(
        github_webhook_service.github_service,
        "installation_client_for_repository",
        lambda db, current_repository_id: SimpleNamespace(
            get_pull_request_context=lambda owner, name, pr_number: (
                _pull_request_context(number=pr_number)
            )
        ),
    )
    monkeypatch.setattr(
        github_webhook_service.analysis_service,
        "get_analysis_run_by_pr_head",
        lambda db, current_repository_id, pr_number, head_sha: None,
    )
    monkeypatch.setattr(
        github_webhook_service.analysis_service,
        "create_or_reuse_webhook_analysis_run",
        lambda db, current_repository_id, context: SimpleNamespace(
            id=analysis_run_id,
            status=AnalysisRunStatus.PENDING,
        ),
    )
    monkeypatch.setattr(
        github_webhook_service,
        "_execute_run_by_id",
        lambda current_analysis_run_id: scheduled.append(current_analysis_run_id),
    )

    class ImmediateBackgroundTasks:
        def add_task(self, function, *args):
            function(*args)

    result = github_webhook_service.process_github_webhook(
        object(),
        body,
        "pull_request",
        "sha256=test",
        background_tasks=ImmediateBackgroundTasks(),
    )

    assert result.analysis_run_id == analysis_run_id
    assert scheduled == [analysis_run_id]
    get_settings.cache_clear()


def test_pull_request_webhook_is_idempotent_for_same_repository_pr_and_head_sha(
    client, repository, webhook_secret, monkeypatch
):
    current_sha = {"value": "abc123"}
    monkeypatch.setattr(
        "app.services.analysis_execution_service.execute_analysis_run",
        lambda db, analysis_run_id: None,
    )

    from app.services.github_service import GitHubClient

    def fake_context(self, owner, name, pr_number):
        return _pull_request_context(head_sha=current_sha["value"], number=pr_number)

    monkeypatch.setattr(
        GitHubClient, "get_pull_request_context", fake_context, raising=False
    )

    first = _post_webhook(client, _pull_request_payload(head_sha="abc123")).json()
    second = _post_webhook(client, _pull_request_payload(head_sha="abc123")).json()

    assert second["analysis_run_id"] == first["analysis_run_id"]

    current_sha["value"] = "def456"
    third = _post_webhook(client, _pull_request_payload(head_sha="def456")).json()

    assert third["analysis_run_id"] != first["analysis_run_id"]
    runs = client.get(f"/api/repositories/{repository['id']}/analysis-runs").json()
    assert len(runs) == 2
    assert {run["head_sha"] for run in runs} == {"abc123", "def456"}


def test_webhook_enrichment_failure_creates_error_run(
    client, repository, webhook_secret, monkeypatch
):
    from app.services.github_service import GitHubClient

    def fail_context(self, owner, name, pr_number):
        raise AppError(502, "github_request_failed", "GitHub API request failed.")

    monkeypatch.setattr(
        GitHubClient, "get_pull_request_context", fail_context, raising=False
    )

    response = _post_webhook(client, _pull_request_payload(head_sha="abc123"))

    assert response.status_code == 202
    body = response.json()
    assert body["ignored"] is False
    run = client.get(f"/api/analysis-runs/{body['analysis_run_id']}").json()
    assert run["status"] == "error"
    assert run["decision"] is None
    assert run["trigger_source"] == "github_webhook"
    assert run["error_message"] == ENRICHMENT_ERROR

    replay = _post_webhook(client, _pull_request_payload(head_sha="abc123")).json()
    assert replay["analysis_run_id"] == body["analysis_run_id"]
