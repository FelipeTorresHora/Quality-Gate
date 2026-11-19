from types import SimpleNamespace

import pytest

from app.core.errors import AppError
from app.db.session import SessionLocal
from app.models.analysis_run import AnalysisRun
from app.models.enums import (
    AnalysisRunStatus,
    AnalysisTriggerSource,
    FindingCategory,
    FindingSeverity,
    GateDecision,
)
from app.models.repository import Repository
from app.models.user import User
from app.services import (
    github_app_auth_service,
    github_installation_service,
    session_service,
)
from app.services.agent.schemas import (
    AICoverageReview,
    AIGateFinding,
    AIReviewGenerated,
    AIReviewPartial,
    AISecurityReview,
    AITechDebtReview,
    ContextBudgetMetadata,
    InlineComment,
    PillarInsights,
    TriagedAlert,
)
from app.services.report_service import build_final_report


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


def _create_run(
    repository,
    *,
    status=AnalysisRunStatus.COMPLETED,
    decision=GateDecision.PASS,
    final_report_markdown="# AI Quality Gate: PASS\n\nReport body.",
    ai_review_json=None,
):
    with SessionLocal() as db:
        run = AnalysisRun(
            repository_id=repository["id"],
            pr_number=42,
            head_sha="abc123",
            status=status,
            decision=decision,
            trigger_source=AnalysisTriggerSource.GITHUB_WEBHOOK,
            final_report_markdown=final_report_markdown,
            pull_request_snapshot_json={
                "number": 42,
                "title": "Add feature",
                "html_url": "https://github.com/horinha04/meu-projeto/pull/42",
            },
            changed_files_snapshot_json=[],
            diff_snapshot="diff --git",
            diff_truncated=False,
            ai_review_json=ai_review_json or {},
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


def test_publish_redacts_pull_request_comment_body(
    client,
    publication_repository,
    monkeypatch,
):
    run_id = _create_run(
        publication_repository,
        final_report_markdown=(
            "# AI Quality Gate: FAIL\n\n"
            "Token leaked: github_pat_abcdefghijklmnopqrstuv_wxyz1234567890\n"
        ),
    )
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
    assert "github_pat_abcdefghijklmnopqrstuv" not in created["body"]
    assert "***REDACTED***" in created["body"]
    assert f"<!-- ai-quality-gate:analysis-run:{run_id} -->" in created["body"]


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

    def fake_status(self, owner, name, sha, state, context, description, target_url=None):
        published.update(
            {
                "owner": owner,
                "name": name,
                "sha": sha,
                "state": state,
                "context": context,
                "description": description,
                "target_url": target_url,
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
    assert published["target_url"] == f"http://localhost:5173/analysis-runs/{run_id}"
    assert response.json()["commit_status"]["published"] is True
    assert response.json()["commit_status"]["state"] == "failure"
    assert response.json()["commit_status"]["target_url"] == published["target_url"]
    assert "/check-runs" not in published["target_url"]


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


def test_create_commit_status_uses_statuses_api_not_checks(
    monkeypatch,
):
    from app.services.github_service import GitHubClient

    captured = {}

    class FakeResponse:
        status_code = 201
        is_error = False
        headers = {}

        def json(self):
            return {"state": "pending"}

    def fake_post(url, headers=None, json=None, timeout=None):
        captured["url"] = url
        captured["json"] = json
        return FakeResponse()

    monkeypatch.setattr("app.services.github_service.httpx.post", fake_post)
    GitHubClient("installation-token").create_commit_status(
        "horinha04",
        "meu-projeto",
        "abc123",
        "pending",
        "ai-quality-gate",
        "Quality gate running.",
        "http://localhost:5173/analysis-runs/run-id",
    )

    assert captured["url"].endswith(
        "/repos/horinha04/meu-projeto/statuses/abc123"
    )
    assert "check-runs" not in captured["url"]
    assert captured["json"] == {
        "state": "pending",
        "context": "ai-quality-gate",
        "description": "Quality gate running.",
        "target_url": "http://localhost:5173/analysis-runs/run-id",
    }


def _raise_installation_token_error():
    raise AppError(
        503,
        "github_installation_token_failed",
        "GitHub installation token could not be generated.",
    )


def test_analysis_run_target_url_uses_vercel_production_host(monkeypatch):
    from uuid import UUID

    from app.services.github_publication_service import analysis_run_target_url

    run_id = UUID("00000000-0000-0000-0000-000000000001")
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setenv(
        "VERCEL_PROJECT_PRODUCTION_URL",
        "quality-gate-gamma.vercel.app",
    )
    monkeypatch.setenv(
        "FRONTEND_ORIGIN",
        "https://quality-gate-git-cursor-preview.vercel.app",
    )
    get_settings = __import__(
        "app.core.config", fromlist=["get_settings"]
    ).get_settings
    get_settings.cache_clear()

    assert (
        analysis_run_target_url(run_id)
        == f"https://quality-gate-gamma.vercel.app/analysis-runs/{run_id}"
    )
    get_settings.cache_clear()


def test_analysis_run_target_url_uses_frontend_origin_locally(monkeypatch):
    from uuid import UUID

    from app.services.github_publication_service import analysis_run_target_url

    run_id = UUID("00000000-0000-0000-0000-000000000002")
    monkeypatch.delenv("VERCEL", raising=False)
    monkeypatch.delenv("VERCEL_PROJECT_PRODUCTION_URL", raising=False)
    monkeypatch.setenv("FRONTEND_ORIGIN", "http://localhost:5173")
    get_settings = __import__(
        "app.core.config", fromlist=["get_settings"]
    ).get_settings
    get_settings.cache_clear()

    assert (
        analysis_run_target_url(run_id)
        == f"http://localhost:5173/analysis-runs/{run_id}"
    )
    get_settings.cache_clear()


def _publish(client, repository, run_id):
    return client.post(
        f"/api/analysis-runs/{run_id}/publish-github",
        cookies={
            "qg_session": repository["cookie"],
            "qg_csrf": repository["csrf_token"],
        },
        headers={"X-CSRF-Token": repository["csrf_token"]},
    )


def _generated_review(**overrides):
    payload = dict(
        score=81,
        summary="Review the helper before merging.",
        risk_level="high",
        coverage_assessment="Top-level coverage.",
        security_assessment="Top-level security.",
        technical_debt_assessment="Top-level debt.",
    )
    payload.update(overrides)
    return AIReviewGenerated(**payload)


def _inline(path, line, title, body, **overrides):
    return InlineComment(
        file_path=path,
        line_number=line,
        title=title,
        body=body,
        confidence=0.8,
        **overrides,
    )


class _FakeGitHubResponse:
    def __init__(self, status_code, payload=None):
        self.status_code = status_code
        self.is_error = status_code >= 400
        self.headers = {}
        self._payload = payload or {}

    def json(self):
        return self._payload


def test_create_pull_request_review_posts_comment_review(monkeypatch):
    from app.services.github_service import GitHubClient

    captured = {}

    def fake_post(url, headers=None, json=None, timeout=None):
        captured["url"] = url
        captured["json"] = json
        captured["timeout"] = timeout
        return _FakeGitHubResponse(201, {"id": 9, "html_url": "https://github.com/review/9"})

    monkeypatch.setattr("app.services.github_service.httpx.post", fake_post)
    result = GitHubClient("installation-token").create_pull_request_review(
        "horinha04",
        "meu-projeto",
        42,
        "abc123",
        "Review body",
        [
            {
                "path": "app/service.py",
                "line": 12,
                "side": "LEFT",
                "body": "Rename the helper.",
            }
        ],
    )

    assert result["html_url"] == "https://github.com/review/9"
    assert captured["url"] == (
        "https://api.github.com/repos/horinha04/meu-projeto/pulls/42/reviews"
    )
    assert captured["timeout"] == 20
    assert captured["json"] == {
        "commit_id": "abc123",
        "body": "Review body",
        "event": "COMMENT",
        "comments": [
            {
                "path": "app/service.py",
                "line": 12,
                "side": "RIGHT",
                "body": "Rename the helper.",
            }
        ],
    }


def test_create_pull_request_review_rejects_unprocessable_line(monkeypatch):
    from app.services.github_service import GitHubClient

    monkeypatch.setattr(
        "app.services.github_service.httpx.post",
        lambda url, headers=None, json=None, timeout=None: _FakeGitHubResponse(422),
    )

    with pytest.raises(AppError) as exc:
        GitHubClient("installation-token").create_pull_request_review(
            "horinha04",
            "meu-projeto",
            42,
            "abc123",
            "Review body",
            [{"path": "app/service.py", "line": 12, "body": "Rename the helper."}],
        )

    assert exc.value.status_code == 422
    assert exc.value.code == "github_pull_request_review_rejected"


def test_create_pull_request_review_maps_other_errors(monkeypatch):
    from app.services.github_service import GitHubClient

    monkeypatch.setattr(
        "app.services.github_service.httpx.post",
        lambda url, headers=None, json=None, timeout=None: _FakeGitHubResponse(500),
    )

    with pytest.raises(AppError) as exc:
        GitHubClient("installation-token").create_pull_request_review(
            "horinha04",
            "meu-projeto",
            42,
            "abc123",
            "Review body",
            [],
        )

    assert exc.value.status_code == 502
    assert exc.value.code == "github_request_failed"


def _unexpected_call(message):
    def _fail(*args, **kwargs):
        raise AssertionError(message)

    return _fail


def test_publish_creates_one_review_for_validated_inline_comments(
    client,
    publication_repository,
    monkeypatch,
):
    review = _generated_review(
        inline_comments=[
            _inline(
                "app/service.py",
                12,
                "Rename helper",
                "Token leaked: github_pat_abcdefghijklmnopqrstuv_wxyz1234567890",
                suggestion_code="def specific_name():\n    return 1",
                severity=FindingSeverity.HIGH,
            ),
            _inline("app/other.py", 4, "Drop the flag", "The flag is unused."),
        ]
    )
    run_id = _create_run(
        publication_repository,
        ai_review_json=review.model_dump(mode="json"),
    )
    _set_publish_flags(
        client,
        publication_repository,
        comment=True,
        status=True,
    )
    published = {}

    from app.services.github_service import GitHubClient

    def fake_review(self, owner, name, pr_number, commit_id, body, comments):
        published["review"] = {
            "owner": owner,
            "name": name,
            "pr_number": pr_number,
            "commit_id": commit_id,
            "body": body,
            "comments": comments,
        }
        return {"id": 9, "html_url": "https://github.com/review/9"}

    def fake_status(self, owner, name, sha, state, context, description, target_url=None):
        published["status"] = {
            "sha": sha,
            "state": state,
            "context": context,
            "description": description,
            "target_url": target_url,
        }
        return {"state": state}

    monkeypatch.setattr(GitHubClient, "create_pull_request_review", fake_review)
    monkeypatch.setattr(GitHubClient, "create_commit_status", fake_status)
    monkeypatch.setattr(
        GitHubClient,
        "create_issue_comment",
        _unexpected_call("issue comment must not be used when a review is accepted"),
    )
    monkeypatch.setattr(
        GitHubClient,
        "list_issue_comments",
        _unexpected_call("issue comment must not be used when a review is accepted"),
    )

    response = _publish(client, publication_repository, run_id)

    assert response.status_code == 200
    review_call = published["review"]
    assert review_call["owner"] == "horinha04"
    assert review_call["name"] == "meu-projeto"
    assert review_call["pr_number"] == 42
    assert review_call["commit_id"] == "abc123"
    assert f"<!-- ai-quality-gate:analysis-run:{run_id} -->" in review_call["body"]
    assert review_call["comments"] == [
        {
            "path": "app/service.py",
            "line": 12,
            "body": (
                "**Rename helper** (high)\n\n"
                "Token leaked: ***REDACTED***\n\n"
                "```suggestion\n"
                "def specific_name():\n"
                "    return 1\n"
                "```"
            ),
        },
        {
            "path": "app/other.py",
            "line": 4,
            "body": "**Drop the flag** (medium)\n\nThe flag is unused.",
        },
    ]
    assert "github_pat_abcdefghijklmnopqrstuv" not in review_call["comments"][0]["body"]
    assert published["status"]["state"] == "success"
    assert published["status"]["context"] == "ai-quality-gate"
    assert published["status"]["sha"] == "abc123"
    assert response.json()["comment"]["published"] is True
    assert response.json()["comment"]["html_url"] == "https://github.com/review/9"
    assert response.json()["commit_status"]["published"] is True
    with SessionLocal() as db:
        stored = db.get(AnalysisRun, run_id)
        assert stored.decision == GateDecision.PASS
        assert stored.status == AnalysisRunStatus.COMPLETED


def test_publish_partial_snapshot_with_comments_posts_one_review(
    client,
    publication_repository,
    monkeypatch,
):
    review = AIReviewPartial(
        summary="Stopped early.",
        inline_comments=[
            _inline("app/partial.py", 3, "Name the constant", "Avoid a magic number.")
        ],
        context_budget=ContextBudgetMetadata(
            batches_sent=1,
            batches_total=3,
            review_truncated=True,
            skipped_files=["app/legacy.py"],
        ),
    )
    run_id = _create_run(
        publication_repository,
        ai_review_json=review.model_dump(mode="json"),
    )
    _set_publish_flags(
        client,
        publication_repository,
        comment=True,
        status=False,
    )
    published = {}

    from app.services.github_service import GitHubClient

    def fake_review(self, owner, name, pr_number, commit_id, body, comments):
        published["commit_id"] = commit_id
        published["comments"] = comments
        published["body"] = body
        return {"html_url": "https://github.com/review/partial"}

    monkeypatch.setattr(GitHubClient, "create_pull_request_review", fake_review)
    monkeypatch.setattr(
        GitHubClient,
        "create_issue_comment",
        _unexpected_call("partial comments must publish a review"),
    )

    response = _publish(client, publication_repository, run_id)

    assert response.status_code == 200
    assert published["commit_id"] == "abc123"
    assert published["comments"][0]["path"] == "app/partial.py"
    assert published["comments"][0]["line"] == 3
    assert f"<!-- ai-quality-gate:analysis-run:{run_id} -->" in published["body"]
    assert response.json()["comment"]["html_url"] == "https://github.com/review/partial"


def test_publish_falls_back_to_issue_comment_when_review_is_rejected(
    client,
    publication_repository,
    monkeypatch,
):
    review = _generated_review(
        inline_comments=[
            _inline("app/service.py", 99, "Missing line", "This line is not in the diff.")
        ]
    )
    run_id = _create_run(
        publication_repository,
        ai_review_json=review.model_dump(mode="json"),
    )
    _set_publish_flags(
        client,
        publication_repository,
        comment=True,
        status=True,
    )
    published = {}

    from app.services.github_service import GitHubClient

    def fake_review(self, owner, name, pr_number, commit_id, body, comments):
        raise AppError(
            422,
            "github_pull_request_review_rejected",
            "GitHub rejected the pull request review.",
        )

    def fake_create(self, owner, name, pr_number, body):
        published["body"] = body
        return {"id": 100, "html_url": "https://github.com/comment/100"}

    def fake_status(self, owner, name, sha, state, context, description, target_url=None):
        published["status"] = state
        return {"state": state}

    monkeypatch.setattr(GitHubClient, "create_pull_request_review", fake_review)
    monkeypatch.setattr(GitHubClient, "list_issue_comments", lambda *args, **kwargs: [])
    monkeypatch.setattr(GitHubClient, "create_issue_comment", fake_create)
    monkeypatch.setattr(GitHubClient, "create_commit_status", fake_status)

    response = _publish(client, publication_repository, run_id)

    assert response.status_code == 200
    assert f"<!-- ai-quality-gate:analysis-run:{run_id} -->" in published["body"]
    assert published["status"] == "success"
    assert response.json()["comment"]["html_url"] == "https://github.com/comment/100"
    assert response.json()["commit_status"]["published"] is True


def test_publish_does_not_fall_back_when_review_fails_for_another_reason(
    client,
    publication_repository,
    monkeypatch,
):
    review = _generated_review(
        inline_comments=[
            _inline("app/service.py", 12, "Rename helper", "Use a specific name.")
        ]
    )
    run_id = _create_run(
        publication_repository,
        ai_review_json=review.model_dump(mode="json"),
    )
    _set_publish_flags(
        client,
        publication_repository,
        comment=True,
        status=True,
    )

    from app.services.github_service import GitHubClient

    def fake_review(self, owner, name, pr_number, commit_id, body, comments):
        raise AppError(502, "github_request_failed", "GitHub API request failed.")

    monkeypatch.setattr(GitHubClient, "create_pull_request_review", fake_review)
    monkeypatch.setattr(
        GitHubClient,
        "create_issue_comment",
        _unexpected_call("non-422 review failures must not fall back"),
    )
    monkeypatch.setattr(
        GitHubClient,
        "create_commit_status",
        _unexpected_call("commit status waits until the comment channel finishes"),
    )

    response = _publish(client, publication_repository, run_id)

    assert response.status_code == 502
    assert response.json()["detail"]["code"] == "github_request_failed"


def test_publish_falls_back_when_snapshot_has_no_valid_inline_comments(
    client,
    publication_repository,
    monkeypatch,
):
    run_id = _create_run(
        publication_repository,
        ai_review_json={
            "status": "generated",
            "summary": "missing required fields",
            "inline_comments": [{"file_path": "app/service.py", "line_number": 4}],
        },
    )
    _set_publish_flags(
        client,
        publication_repository,
        comment=True,
        status=False,
    )
    created = {}

    from app.services.github_service import GitHubClient

    monkeypatch.setattr(GitHubClient, "list_issue_comments", lambda *args, **kwargs: [])

    def fake_create(self, owner, name, pr_number, body):
        created["body"] = body
        return {"id": 100, "html_url": "https://github.com/comment/100"}

    monkeypatch.setattr(GitHubClient, "create_issue_comment", fake_create)
    monkeypatch.setattr(
        GitHubClient,
        "create_pull_request_review",
        _unexpected_call("invalid inline comments must use the issue comment"),
    )

    response = _publish(client, publication_repository, run_id)

    assert response.status_code == 200
    assert f"<!-- ai-quality-gate:analysis-run:{run_id} -->" in created["body"]
    assert response.json()["comment"]["html_url"] == "https://github.com/comment/100"


def test_publish_falls_back_when_partial_review_has_no_comments(
    client,
    publication_repository,
    monkeypatch,
):
    review = AIReviewPartial(
        summary="Stopped early.",
        context_budget=ContextBudgetMetadata(
            batches_sent=1,
            batches_total=2,
            review_truncated=True,
            skipped_files=["app/legacy.py"],
        ),
    )
    run_id = _create_run(
        publication_repository,
        ai_review_json=review.model_dump(mode="json"),
    )
    _set_publish_flags(
        client,
        publication_repository,
        comment=True,
        status=False,
    )
    created = {}

    from app.services.github_service import GitHubClient

    monkeypatch.setattr(GitHubClient, "list_issue_comments", lambda *args, **kwargs: [])

    def fake_create(self, owner, name, pr_number, body):
        created["body"] = body
        return {"html_url": "https://github.com/comment/empty"}

    monkeypatch.setattr(GitHubClient, "create_issue_comment", fake_create)
    monkeypatch.setattr(
        GitHubClient,
        "create_pull_request_review",
        _unexpected_call("an empty comment list must use the issue comment"),
    )

    response = _publish(client, publication_repository, run_id)

    assert response.status_code == 200
    assert f"<!-- ai-quality-gate:analysis-run:{run_id} -->" in created["body"]


def _report_run(**overrides):
    run = SimpleNamespace(
        status=AnalysisRunStatus.COMPLETED,
        decision=GateDecision.PASS,
        score=88,
        coverage_result_json={"status": "pass"},
        security_result_json={"status": "pass"},
        technical_debt_result_json={"status": "pass"},
        findings=[],
    )
    for key, value in overrides.items():
        setattr(run, key, value)
    return run


def _ai_finding(category, title, file_path=None, line_number=None):
    return AIGateFinding(
        category=category,
        severity=FindingSeverity.LOW,
        file_path=file_path,
        line_number=line_number,
        title=title,
        description="Non-blocking AI note.",
        confidence=0.4,
    )


def test_report_renders_code_review_pillar_insights_and_truncated_files():
    review = _generated_review(
        inline_comments=[
            _inline(
                "app/service.py",
                12,
                "Rename helper",
                "Use a specific name.",
                suggestion_code="specific_name",
                severity=FindingSeverity.HIGH,
            ),
            _inline("app/other.py", 4, "Drop the flag", "The flag is unused."),
        ],
        pillar_insights=PillarInsights(
            coverage=AICoverageReview(
                summary="Coverage dropped on the new helper.",
                coverage_assessment="Insight coverage.",
                findings=[
                    _ai_finding(
                        FindingCategory.COVERAGE,
                        "Uncovered branch",
                        "app/covered.py",
                        8,
                    ),
                    _ai_finding(
                        FindingCategory.COVERAGE,
                        "Uncovered file",
                        "app/covered.py",
                    ),
                    _ai_finding(FindingCategory.COVERAGE, "General coverage note"),
                ],
            ),
            security=AISecurityReview(
                summary="Security looks contained.",
                security_assessment="No new secrets.",
                triaged_alerts=[
                    TriagedAlert(
                        scanner="semgrep",
                        severity=FindingSeverity.HIGH,
                        title="Possible injection",
                        description="User input reaches a shell.",
                        confidence=0.7,
                        disposition="dismiss",
                        rationale="The input is a constant.",
                    ),
                    TriagedAlert(
                        scanner="bandit",
                        severity=FindingSeverity.MEDIUM,
                        title="Assert used",
                        description="Assert is not a guard.",
                        confidence=0.5,
                        disposition="downgrade",
                        rationale="Test-only helper.",
                    ),
                    TriagedAlert(
                        scanner="pip-audit",
                        severity=FindingSeverity.LOW,
                        title="Key shape",
                        description="Looks like a key.",
                        confidence=0.3,
                        disposition="confirm",
                        rationale="It is a fixture.",
                    ),
                ],
                findings=[
                    _ai_finding(FindingCategory.SECURITY, "Security note"),
                ],
            ),
            technical_debt=AITechDebtReview(
                summary="Debt is stable.",
                technical_debt_assessment="",
            ),
        ),
        context_budget=ContextBudgetMetadata(
            batches_sent=1,
            batches_total=3,
            review_truncated=True,
            skipped_files=["app/legacy.py"],
        ),
    )

    report = build_final_report(_report_run(), review.model_dump(mode="json"))

    assert "**Gate Decision:** PASS" in report
    assert "Review the helper before merging." in report
    assert "Top-level coverage." in report
    assert "## Code Review" in report
    assert "**app/service.py:12** (high) Rename helper: Use a specific name." in report
    assert "Suggestion: `specific_name`" in report
    assert "**app/other.py:4** (medium) Drop the flag: The flag is unused." in report
    assert "AI insight: Coverage dropped on the new helper." in report
    assert "Insight coverage." in report
    assert "- Uncovered branch (app/covered.py:8): Non-blocking AI note." in report
    assert "- Uncovered file (app/covered.py): Non-blocking AI note." in report
    assert "- General coverage note: Non-blocking AI note." in report
    assert "AI insight: Security looks contained." in report
    assert "- dismiss: Possible injection: The input is a constant." in report
    assert "- downgrade: Assert used: Test-only helper." in report
    assert "- confirm: Key shape: It is a fixture." in report
    assert "AI insight: Debt is stable." in report
    assert "AI insight: not reviewed." not in report
    assert "## Context budget" in report
    assert "Batches sent: 1 of 3." in report
    assert "Review truncated: yes" in report
    assert "- `app/legacy.py`" in report


def test_report_partial_state_includes_empty_review_sections():
    empty = AIReviewPartial(
        summary="   ",
        context_budget=ContextBudgetMetadata(
            batches_sent=1,
            batches_total=1,
            review_truncated=False,
        ),
    )
    empty_report = build_final_report(_report_run(), empty.model_dump(mode="json"))
    assert (
        empty_report.count(
            "AI review is partial because the context budget was exhausted."
        )
        == 1
    )
    assert "Stopped" not in empty_report
    assert "## Code Review\n\nNone." in empty_report
    assert empty_report.count("AI insight: not reviewed.") == 3
    assert "Review truncated: no" in empty_report
    assert "Skipped files:" not in empty_report

    stopped = AIReviewPartial(
        summary="Stopped early.",
        inline_comments=[
            _inline("app/partial.py", 3, "Name the constant", "Avoid a magic number.")
        ],
        context_budget=ContextBudgetMetadata(
            batches_sent=1,
            batches_total=4,
            review_truncated=True,
            skipped_files=["app/legacy.py", "lib/old.go"],
        ),
    )
    report = build_final_report(
        _report_run(decision=GateDecision.FAIL),
        stopped.model_dump(mode="json"),
    )
    assert (
        "AI review is partial because the context budget was exhausted. Stopped early."
        in report
    )
    assert "**Gate Decision:** FAIL" in report
    assert "**app/partial.py:3** (medium) Name the constant: Avoid a magic number." in report
    assert "- `lib/old.go`" in report


def test_report_omits_review_sections_without_new_snapshot_fields():
    plain = build_final_report(_report_run(), {})
    assert "passed their configured policies" in plain
    assert "## Code Review" not in plain
    assert "AI insight:" not in plain
    assert "## Context budget" not in plain

    untouched = _generated_review(
        context_budget=ContextBudgetMetadata(
            batches_sent=1,
            batches_total=1,
            review_truncated=False,
        )
    )
    quiet = build_final_report(_report_run(), untouched.model_dump(mode="json"))
    assert "Review the helper before merging." in quiet
    assert "## Code Review" not in quiet
    assert "AI insight:" not in quiet
    assert "## Context budget" not in quiet

    truncated = _generated_review(
        summary="",
        context_budget=ContextBudgetMetadata(
            batches_sent=1,
            batches_total=2,
            review_truncated=True,
        ),
    )
    truncated_report = build_final_report(
        _report_run(),
        truncated.model_dump(mode="json"),
    )
    assert "passed their configured policies" in truncated_report
    assert "Review truncated: yes" in truncated_report
    assert "Skipped files:\nNone." in truncated_report

    invalid = build_final_report(
        _report_run(),
        {"status": "generated", "summary": "dict summary", "score": "bad"},
    )
    assert "dict summary" in invalid
    assert "**Gate Decision:** PASS" in invalid
