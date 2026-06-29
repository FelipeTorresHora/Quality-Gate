import pytest

from app.core.errors import AppError
from app.db.session import SessionLocal
from app.models.analysis_run import AnalysisRun
from app.models.enums import AnalysisRunStatus, AnalysisTriggerSource, GateDecision
from app.models.repository import Repository
from app.models.user import User
from app.services import (
    github_app_auth_service,
    github_installation_service,
    session_service,
)


@pytest.fixture
def publication_repository(reset_database, db_session):
    user = User(github_user_id=501, github_login="publisher")
    db_session.add(user)
    db_session.commit()
    github_installation_service.sync_installation_payload(
        db_session,
        user=user,
        installation_payload={
            "id": 601,
            "account": {
                "id": 701,
                "login": "horinha04",
                "type": "Organization",
            },
            "repository_selection": "selected",
            "permissions": {
                "contents": "read",
                "pull_requests": "write",
                "statuses": "write",
            },
            "events": ["pull_request"],
        },
        repositories_payload=[
            {
                "id": 801,
                "name": "meu-projeto",
                "full_name": "horinha04/meu-projeto",
                "owner": {"login": "horinha04"},
                "default_branch": "main",
                "permissions": {
                    "admin": True,
                    "push": True,
                    "pull": True,
                },
            }
        ],
    )
    repository = db_session.query(Repository).filter_by(
        full_name="horinha04/meu-projeto"
    ).one()
    created = session_service.create_session(db_session, user)
    return {
        "id": str(repository.id),
        "cookie": created.cookie_value,
        "csrf_token": created.csrf_token,
    }


@pytest.fixture(autouse=True)
def installation_token(monkeypatch):
    monkeypatch.setattr(
        github_app_auth_service,
        "generate_installation_token",
        lambda installation_id: f"installation-token-{installation_id}",
    )


def _create_run(repository, *, status=AnalysisRunStatus.COMPLETED, decision=GateDecision.PASS):
    with SessionLocal() as db:
        run = AnalysisRun(
            repository_id=repository["id"],
            pr_number=42,
            head_sha="abc123",
            status=status,
            decision=decision,
            trigger_source=AnalysisTriggerSource.GITHUB_WEBHOOK,
            final_report_markdown="# AI Quality Gate: PASS\n\nReport body.",
            pull_request_snapshot_json={
                "number": 42,
                "title": "Add feature",
                "html_url": "https://github.com/horinha04/meu-projeto/pull/42",
            },
            changed_files_snapshot_json=[],
            diff_snapshot="diff --git",
            diff_truncated=False,
        )
        db.add(run)
        db.commit()
        return str(run.id)


def _set_publish_flags(client, repository, *, comment, status):
    response = client.put(
        f"/api/repositories/{repository['id']}/quality-gate-config",
        cookies={
            "qg_session": repository["cookie"],
            "qg_csrf": repository["csrf_token"],
        },
        headers={"X-CSRF-Token": repository["csrf_token"]},
        json={
            "comment_on_github": comment,
            "publish_github_status": status,
        },
    )
    assert response.status_code == 200


def test_publish_rejects_pending_run(client, publication_repository):
    run_id = _create_run(
        publication_repository,
        status=AnalysisRunStatus.PENDING,
        decision=None,
    )

    response = client.post(
        f"/api/analysis-runs/{run_id}/publish-github",
        cookies={
            "qg_session": publication_repository["cookie"],
            "qg_csrf": publication_repository["csrf_token"],
        },
        headers={"X-CSRF-Token": publication_repository["csrf_token"]},
    )

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "analysis_run_not_publishable"


def test_publish_skips_disabled_channels(client, publication_repository):
    run_id = _create_run(publication_repository)
    _set_publish_flags(
        client,
        publication_repository,
        comment=False,
        status=False,
    )

    response = client.post(
        f"/api/analysis-runs/{run_id}/publish-github",
        cookies={
            "qg_session": publication_repository["cookie"],
            "qg_csrf": publication_repository["csrf_token"],
        },
        headers={"X-CSRF-Token": publication_repository["csrf_token"]},
    )

    assert response.status_code == 200
    result = response.json()
    assert result["analysis_run_id"] == run_id
    assert result["comment"] == {
        "enabled": False,
        "published": False,
        "html_url": None,
        "skipped_reason": "comment_disabled",
    }
    assert result["commit_status"]["enabled"] is False
    assert result["commit_status"]["published"] is False
    assert result["commit_status"]["skipped_reason"] == "status_disabled"


def test_publish_creates_marked_pull_request_comment(
    client,
    publication_repository,
    monkeypatch,
):
    run_id = _create_run(publication_repository)
    _set_publish_flags(
        client,
        publication_repository,
        comment=True,
        status=False,
    )
    created = {}

    from app.services.github_service import GitHubClient

    monkeypatch.setattr(
        GitHubClient,
        "list_issue_comments",
        lambda self, owner, name, pr_number: [],
    )

    def fake_create(self, owner, name, pr_number, body):
        created["owner"] = owner
        created["name"] = name
        created["pr_number"] = pr_number
        created["body"] = body
        return {"id": 100, "html_url": "https://github.com/comment/100"}

    monkeypatch.setattr(GitHubClient, "create_issue_comment", fake_create)

    response = client.post(
        f"/api/analysis-runs/{run_id}/publish-github",
        cookies={
            "qg_session": publication_repository["cookie"],
            "qg_csrf": publication_repository["csrf_token"],
        },
        headers={"X-CSRF-Token": publication_repository["csrf_token"]},
    )

    assert response.status_code == 200
    assert f"<!-- ai-quality-gate:analysis-run:{run_id} -->" in created["body"]
    assert created["pr_number"] == 42
    assert response.json()["comment"]["published"] is True
    assert response.json()["comment"]["html_url"] == "https://github.com/comment/100"


def test_publish_updates_existing_marked_pull_request_comment(
    client,
    publication_repository,
    monkeypatch,
):
    run_id = _create_run(publication_repository)
    _set_publish_flags(
        client,
        publication_repository,
        comment=True,
        status=False,
    )
    updated = {}

    from app.services.github_service import GitHubClient

    monkeypatch.setattr(
        GitHubClient,
        "list_issue_comments",
        lambda self, owner, name, pr_number: [
            {
                "id": 101,
                "body": f"old\n<!-- ai-quality-gate:analysis-run:{run_id} -->",
                "html_url": "https://github.com/comment/101",
            }
        ],
    )

    def fake_update(self, owner, name, comment_id, body):
        updated["comment_id"] = comment_id
        updated["body"] = body
        return {"id": comment_id, "html_url": "https://github.com/comment/101"}

    monkeypatch.setattr(GitHubClient, "update_issue_comment", fake_update)

    response = client.post(
        f"/api/analysis-runs/{run_id}/publish-github",
        cookies={
            "qg_session": publication_repository["cookie"],
            "qg_csrf": publication_repository["csrf_token"],
        },
        headers={"X-CSRF-Token": publication_repository["csrf_token"]},
    )

    assert response.status_code == 200
    assert updated["comment_id"] == 101
    assert f"<!-- ai-quality-gate:analysis-run:{run_id} -->" in updated["body"]
    assert response.json()["comment"]["html_url"] == "https://github.com/comment/101"


def test_publish_commit_status_maps_decision(
    client,
    publication_repository,
    monkeypatch,
):
    run_id = _create_run(
        publication_repository,
        decision=GateDecision.FAIL,
    )
    _set_publish_flags(
        client,
        publication_repository,
        comment=False,
        status=True,
    )
    published = {}

    from app.services.github_service import GitHubClient

    def fake_status(self, owner, name, sha, state, context, description):
        published.update(
            {
                "owner": owner,
                "name": name,
                "sha": sha,
                "state": state,
                "context": context,
                "description": description,
            }
        )
        return {"state": state}

    monkeypatch.setattr(GitHubClient, "create_commit_status", fake_status)

    response = client.post(
        f"/api/analysis-runs/{run_id}/publish-github",
        cookies={
            "qg_session": publication_repository["cookie"],
            "qg_csrf": publication_repository["csrf_token"],
        },
        headers={"X-CSRF-Token": publication_repository["csrf_token"]},
    )

    assert response.status_code == 200
    assert published["sha"] == "abc123"
    assert published["state"] == "failure"
    assert published["context"] == "ai-quality-gate"
    assert published["description"] == "Quality gate failed."
    assert response.json()["commit_status"]["published"] is True
    assert response.json()["commit_status"]["state"] == "failure"


def test_publish_installation_token_failure_returns_stable_error(
    client,
    publication_repository,
    monkeypatch,
):
    run_id = _create_run(publication_repository)
    _set_publish_flags(
        client,
        publication_repository,
        comment=True,
        status=False,
    )
    monkeypatch.setattr(
        github_app_auth_service,
        "generate_installation_token",
        lambda installation_id: _raise_installation_token_error(),
    )

    response = client.post(
        f"/api/analysis-runs/{run_id}/publish-github",
        cookies={
            "qg_session": publication_repository["cookie"],
            "qg_csrf": publication_repository["csrf_token"],
        },
        headers={"X-CSRF-Token": publication_repository["csrf_token"]},
    )

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "github_installation_token_failed"


def _raise_installation_token_error():
    raise AppError(
        503,
        "github_installation_token_failed",
        "GitHub installation token could not be generated.",
    )
