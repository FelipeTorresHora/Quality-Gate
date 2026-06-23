from uuid import UUID

from app.models.analysis_run import AnalysisRun
from app.models.enums import AnalysisTriggerSource


def test_manual_analyze_requires_repository_access(client):
    repository_id = UUID("00000000-0000-0000-0000-000000000001")

    response = client.post(
        f"/api/repositories/{repository_id}/pull-requests/1/analyze"
    )

    assert response.status_code == 401


def test_manual_analyze_creates_and_executes_real_run(
    monkeypatch,
    client,
    reset_database,
    db_session,
    create_user_repo_access,
):
    _user, repository, cookie = create_user_repo_access(is_admin=False)

    monkeypatch.setattr(
        "app.services.github_service.get_repository_pull_request_context",
        lambda db, repository_id, pr_number: {
            "pull_request": {
                "number": pr_number,
                "title": "Improve quality",
                "body": None,
                "state": "open",
                "draft": False,
                "author_login": "octocat",
                "html_url": (
                    "https://github.com/octo-org/quality-api/pull/1"
                ),
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
        lambda db, analysis_run_id: db.get(AnalysisRun, analysis_run_id),
    )

    response = client.post(
        f"/api/repositories/{repository.id}/pull-requests/1/analyze",
        cookies={"qg_session": cookie},
    )

    assert response.status_code == 200
    assert (
        response.json()["trigger_source"]
        == AnalysisTriggerSource.MANUAL.value
    )
