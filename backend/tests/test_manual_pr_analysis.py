from uuid import UUID
from types import SimpleNamespace

from app.models.analysis_run import AnalysisRun
from app.models.enums import AnalysisTriggerSource


def test_manual_analyze_requires_repository_access(client):
    repository_id = UUID("00000000-0000-0000-0000-000000000001")

    response = client.post(
        f"/api/repositories/{repository_id}/pull-requests/1/analyze"
    )

    assert response.status_code == 401


def test_manual_analyze_enqueues_pending_run(
    monkeypatch,
    client,
    reset_database,
    db_session,
    create_user_repo_access,
):
    _user, repository, cookie, csrf_token = create_user_repo_access(is_admin=False)

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
    enqueued = []
    monkeypatch.setattr(
        "app.services.analysis_queue.enqueue",
        lambda run_id: enqueued.append(str(run_id)),
    )

    response = client.post(
        f"/api/repositories/{repository.id}/pull-requests/1/analyze",
        cookies={"qg_session": cookie, "qg_csrf": csrf_token},
        headers={"X-CSRF-Token": csrf_token},
    )

    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "pending"
    assert body["trigger_source"] == AnalysisTriggerSource.MANUAL.value
    assert enqueued == [body["id"]]


def test_manual_analyze_uses_coverage_working_directory_for_nested_project(
    monkeypatch,
    client,
    repository,
    db_session,
    tmp_path,
):
    from app.models.coverage_execution_config import CoverageExecutionConfig
    from app.models.quality_gate_config import QualityGateConfig
    from app.services import analysis_evidence_workspace

    coverage_config = db_session.query(CoverageExecutionConfig).filter_by(
        repository_id=repository["id"]
    ).one()
    coverage_config.working_directory = "docker-log-watcher-agent"
    quality_config = db_session.query(QualityGateConfig).filter_by(
        repository_id=repository["id"]
    ).one()
    quality_config.min_changed_files_coverage = 0
    quality_config.security_enabled = False
    quality_config.technical_debt_enabled = False
    db_session.commit()

    monkeypatch.setattr(
        "app.services.github_service.get_repository_pull_request_context",
        lambda db, repository_id, pr_number: {
            "pull_request": {
                "number": pr_number,
                "title": "Exercise nested project analysis",
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
                "created_at": "2026-06-30T00:00:00Z",
                "updated_at": "2026-06-30T00:00:00Z",
            },
            "changed_files": [
                {
                    "filename": "docker-log-watcher-agent/main.py",
                    "status": "modified",
                    "additions": 1,
                    "deletions": 0,
                    "changes": 1,
                    "patch": "@@ -1 +1 @@\n+print('ok')",
                }
            ],
            "diff_snapshot": (
                "diff --git a/docker-log-watcher-agent/main.py "
                "b/docker-log-watcher-agent/main.py"
            ),
            "diff_truncated": False,
        },
    )

    class FakeRunnerWorkspace:
        def __init__(self, analysis_run_id, repository_url):
            self.root = tmp_path / str(analysis_run_id)
            self.repo_path = self.root / "repo"
            self.command_metadata = []

        def __enter__(self):
            self.root.mkdir(parents=True, exist_ok=True)
            return self

        def __exit__(self, exc_type, exc, traceback):
            return None

        def checkout(self, revision):
            (self.repo_path / "docker-log-watcher-agent").mkdir(parents=True)
            return None

        def run(self, command, working_directory="."):
            report = self.repo_path / working_directory / "coverage.xml"
            report.write_text(
                """<?xml version="1.0" ?>
<coverage>
  <packages>
    <package>
      <classes>
        <class filename="main.py">
          <lines>
            <line number="1" hits="1"/>
          </lines>
        </class>
      </classes>
    </package>
  </packages>
</coverage>
""",
                encoding="utf-8",
            )
            return SimpleNamespace(timed_out=False, exit_code=0)

    monkeypatch.setattr(
        analysis_evidence_workspace,
        "RunnerWorkspace",
        FakeRunnerWorkspace,
    )

    response = client.post(
        f"/api/repositories/{repository['id']}/pull-requests/1/analyze",
        headers={"X-CSRF-Token": repository["csrf_token"]},
    )

    assert response.status_code == 202
    run_id = UUID(response.json()["id"])
    assert response.json()["status"] == "pending"

    from app.services import analysis_execution_service

    executed = analysis_execution_service.execute_analysis_run(db_session, run_id)

    assert executed.status.value == "completed"
    assert executed.decision.value == "pass"
    assert executed.coverage_result_json["status"] == "pass"
    assert executed.error_message is None
