from uuid import UUID

import pytest

from app.core.errors import AppError
from app.db.session import SessionLocal
from app.models.analysis_run import AnalysisRun
from app.models.enums import AnalysisRunStatus, AnalysisTriggerSource, FindingCategory
from app.models.quality_gate_config import QualityGateConfig
from app.services import analysis_execution_service
from app.services.github_service import GitHubClient


@pytest.fixture(autouse=True)
def github_writes(monkeypatch):
    calls = {"status": [], "comments": [], "comment_updates": []}

    def fake_status(
        self, owner, name, sha, state, context, description, target_url=None
    ):
        calls["status"].append(
            {
                "sha": sha,
                "state": state,
                "context": context,
                "description": description,
                "target_url": target_url,
            }
        )
        return {"state": state}

    def fake_list(self, owner, name, pr_number):
        return []

    def fake_create(self, owner, name, pr_number, body):
        calls["comments"].append({"pr_number": pr_number, "body": body})
        return {"id": 1, "html_url": "https://github.com/comment/1"}

    def fake_update(self, owner, name, comment_id, body):
        calls["comment_updates"].append({"comment_id": comment_id, "body": body})
        return {"id": comment_id, "html_url": "https://github.com/comment/2"}

    monkeypatch.setattr(GitHubClient, "create_commit_status", fake_status)
    monkeypatch.setattr(GitHubClient, "list_issue_comments", fake_list)
    monkeypatch.setattr(GitHubClient, "create_issue_comment", fake_create)
    monkeypatch.setattr(GitHubClient, "update_issue_comment", fake_update)
    return calls


def _set_publish_flags(repository_id, *, comment, status):
    with SessionLocal() as db:
        config = (
            db.query(QualityGateConfig).filter_by(repository_id=repository_id).one()
        )
        config.comment_on_github = comment
        config.publish_github_status = status
        db.commit()


def _stub_passing_gates(monkeypatch):
    from app.services.gates import coverage_gate, security_gate, technical_debt_gate

    monkeypatch.setattr(
        coverage_gate,
        "run_coverage_gate",
        lambda **kwargs: _gate_result("pass", FindingCategory.COVERAGE),
    )
    monkeypatch.setattr(
        security_gate,
        "run_security_gate",
        lambda **kwargs: _gate_result("pass", FindingCategory.SECURITY),
    )
    monkeypatch.setattr(
        technical_debt_gate,
        "run_technical_debt_gate",
        lambda **kwargs: _gate_result("pass", FindingCategory.TECHNICAL_DEBT),
    )


def _create_run(
    repository,
    *,
    diff_snapshot="diff --git",
    status=AnalysisRunStatus.PENDING,
    started_at=None,
):
    with SessionLocal() as db:
        run = AnalysisRun(
            repository_id=repository["id"],
            pr_number=42,
            head_sha="head123",
            status=status,
            started_at=started_at,
            trigger_source=AnalysisTriggerSource.GITHUB_WEBHOOK,
            pull_request_snapshot_json={
                "number": 42,
                "title": "Add feature",
                "base_sha": "base123",
                "head_sha": "head123",
            },
            changed_files_snapshot_json=[
                {
                    "filename": "src/app.py",
                    "status": "modified",
                    "additions": 1,
                    "deletions": 0,
                    "changes": 1,
                    "patch": "+print('ok')",
                }
            ],
            diff_snapshot=diff_snapshot,
            diff_truncated=False,
        )
        db.add(run)
        db.commit()
        return str(run.id)


def _execute(run_id):
    with SessionLocal() as db:
        result = analysis_execution_service.execute_analysis_run(db, UUID(run_id))
        return {
            "status": result.status.value,
            "decision": result.decision.value if result.decision else None,
            "score": result.score,
            "ai_review_json": result.ai_review_json,
            "started_at": result.started_at,
            "finished_at": result.finished_at,
            "final_report_markdown": result.final_report_markdown,
            "coverage_result_json": result.coverage_result_json,
            "security_result_json": result.security_result_json,
            "technical_debt_result_json": result.technical_debt_result_json,
            "error_message": result.error_message,
            "findings": list(result.findings),
        }


def _gate_result(status="pass", category=FindingCategory.COVERAGE):
    from app.models.enums import FindingSeverity
    from app.services.gates.types import GateFinding, GateResult

    finding = GateFinding(
        category=category,
        severity=FindingSeverity.HIGH,
        file_path="src/app.py",
        line_number=1,
        title=f"{category.value} finding",
        description=f"{category.value} finding",
        blocking=status == "fail",
    )
    return GateResult(
        snapshot={"status": status, "blocking_reasons": [finding.title] if status == "fail" else []},
        findings=[finding] if status == "fail" else [],
        error_message=None,
    )


def test_execute_rejects_non_pending_run(repository):
    run_id = _create_run(repository, status=AnalysisRunStatus.COMPLETED)

    with pytest.raises(AppError) as exc_info:
        _execute(run_id)

    assert exc_info.value.status_code == 409
    assert exc_info.value.code == "analysis_run_not_pending"


def test_execute_marks_error_on_unexpected_exception(repository, monkeypatch):
    run_id = _create_run(repository)

    from app.services.gates import coverage_gate

    def boom(**kwargs):
        raise RuntimeError("scanner crashed")

    monkeypatch.setattr(coverage_gate, "run_coverage_gate", boom)

    run = _execute(run_id)

    assert run["status"] == "error"
    assert "Unexpected analysis failure" in run["error_message"]
    assert "scanner crashed" in run["error_message"]


def test_execute_reruns_stale_running_run(repository, monkeypatch):
    from datetime import UTC, datetime, timedelta

    run_id = _create_run(
        repository,
        status=AnalysisRunStatus.RUNNING,
        started_at=datetime.now(UTC) - timedelta(minutes=31),
    )

    from app.services.gates import coverage_gate, security_gate, technical_debt_gate

    monkeypatch.setattr(
        coverage_gate,
        "run_coverage_gate",
        lambda **kwargs: _gate_result("pass", FindingCategory.COVERAGE),
    )
    monkeypatch.setattr(
        security_gate,
        "run_security_gate",
        lambda **kwargs: _gate_result("pass", FindingCategory.SECURITY),
    )
    monkeypatch.setattr(
        technical_debt_gate,
        "run_technical_debt_gate",
        lambda **kwargs: _gate_result("pass", FindingCategory.TECHNICAL_DEBT),
    )

    run = _execute(run_id)

    assert run["status"] == "completed"


def test_execute_rejects_fresh_running_run(repository):
    from datetime import UTC, datetime

    run_id = _create_run(
        repository,
        status=AnalysisRunStatus.RUNNING,
        started_at=datetime.now(UTC),
    )

    with pytest.raises(AppError) as exc_info:
        _execute(run_id)

    assert exc_info.value.status_code == 409


def test_execute_aborts_when_total_time_budget_exceeded(repository, monkeypatch):
    run_id = _create_run(repository)

    from types import SimpleNamespace

    from app.services import analysis_execution_service
    from app.services.gates import coverage_gate

    monkeypatch.setattr(
        analysis_execution_service,
        "get_settings",
        lambda: SimpleNamespace(analysis_total_timeout_seconds=-1),
    )

    def gate_should_not_run(**kwargs):
        raise AssertionError("gate must not run past the time budget")

    monkeypatch.setattr(coverage_gate, "run_coverage_gate", gate_should_not_run)

    run = _execute(run_id)

    assert run["status"] == "error"
    assert "time budget" in run["error_message"].lower()


def test_execute_pending_run_completes_with_pass(repository, monkeypatch):
    run_id = _create_run(repository)

    from app.models.enums import FindingCategory
    from app.services.gates import coverage_gate, security_gate, technical_debt_gate

    monkeypatch.setattr(
        coverage_gate,
        "run_coverage_gate",
        lambda **kwargs: _gate_result("pass", FindingCategory.COVERAGE),
    )
    monkeypatch.setattr(
        security_gate,
        "run_security_gate",
        lambda **kwargs: _gate_result("pass", FindingCategory.SECURITY),
    )
    monkeypatch.setattr(
        technical_debt_gate,
        "run_technical_debt_gate",
        lambda **kwargs: _gate_result("pass", FindingCategory.TECHNICAL_DEBT),
    )

    run = _execute(run_id)

    assert run["status"] == "completed"
    assert run["decision"] == "pass"
    assert run["score"] is None
    assert run["ai_review_json"]["status"] == "skipped"
    assert run["started_at"] is not None
    assert run["finished_at"] is not None
    assert "# AI Quality Gate: PASS" in run["final_report_markdown"]


def test_execute_reuses_prepared_head_workspace_across_enabled_gates(
    repository,
    monkeypatch,
    tmp_path,
):
    run_id = _create_run(repository)

    from app.services import analysis_evidence_workspace, runner_service
    from app.services.gates import security_gate

    checkouts = []

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
            checkouts.append(revision)
            self.repo_path.mkdir(parents=True, exist_ok=True)
            (self.repo_path / "src").mkdir(parents=True, exist_ok=True)
            (self.repo_path / "src" / "app.py").write_text(
                "def run():\n    return 'ok'\n",
                encoding="utf-8",
            )

        def run(self, command, working_directory="."):
            report = self.repo_path / working_directory / "coverage.xml"
            report.parent.mkdir(parents=True, exist_ok=True)
            report.write_text(
                """<?xml version="1.0" ?>
<coverage>
  <packages>
    <package>
      <classes>
        <class filename="src/app.py">
          <lines>
            <line number="1" hits="1"/>
            <line number="2" hits="1"/>
          </lines>
        </class>
      </classes>
    </package>
  </packages>
</coverage>
""",
                encoding="utf-8",
            )
            return runner_service.CommandResult(
                command=command,
                exit_code=0,
                stdout="{}",
                stderr="",
                duration_seconds=0,
            )

    monkeypatch.setattr(
        analysis_evidence_workspace,
        "RunnerWorkspace",
        FakeRunnerWorkspace,
    )
    monkeypatch.setattr(security_gate, "_scanner_commands", lambda language: [])

    run = _execute(run_id)

    assert run["status"] == "completed"
    assert checkouts.count("head123") == 1
    assert checkouts.count("base123") == 1


def test_execute_marks_runner_timeout_as_operational_error(
    repository,
    monkeypatch,
    tmp_path,
):
    run_id = _create_run(repository)

    from app.services import analysis_evidence_workspace, runner_service

    class TimeoutRunnerWorkspace:
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
            self.repo_path.mkdir(parents=True, exist_ok=True)

        def run(self, command, working_directory="."):
            result = runner_service.CommandResult(
                command=command,
                exit_code=None,
                stdout="",
                stderr="",
                duration_seconds=600,
                timed_out=True,
                adapter="isolated",
                resource_limits={"timeout_seconds": 600},
            )
            self.command_metadata.append(result.to_snapshot())
            return result

    monkeypatch.setattr(
        analysis_evidence_workspace,
        "RunnerWorkspace",
        TimeoutRunnerWorkspace,
    )

    run = _execute(run_id)

    assert run["status"] == "error"
    assert run["decision"] is None
    assert "Coverage" in run["error_message"]
    assert run["coverage_result_json"]["commands"][0]["timed_out"] is True
    assert run["coverage_result_json"]["commands"][0]["runner_adapter"] == "isolated"


def test_execute_pending_run_stores_generated_ai_review_and_score(
    repository, monkeypatch
):
    run_id = _create_run(repository)

    from app.models.enums import FindingCategory
    from app.services.agent import quality_agent
    from app.services.gates import coverage_gate, security_gate, technical_debt_gate

    monkeypatch.setattr(
        coverage_gate,
        "run_coverage_gate",
        lambda **kwargs: _gate_result("pass", FindingCategory.COVERAGE),
    )
    monkeypatch.setattr(
        security_gate,
        "run_security_gate",
        lambda **kwargs: _gate_result("pass", FindingCategory.SECURITY),
    )
    monkeypatch.setattr(
        technical_debt_gate,
        "run_technical_debt_gate",
        lambda **kwargs: _gate_result("pass", FindingCategory.TECHNICAL_DEBT),
    )
    monkeypatch.setattr(
        quality_agent,
        "generate_ai_review_snapshot",
        lambda **kwargs: {
            "status": "generated",
            "model": "gpt-4.1-mini",
            "generated_at": "2026-06-22T12:00:00Z",
            "score": 91,
            "summary": "The PR passes all configured gates.",
            "risk_level": "low",
            "blocking_reasons": [],
            "suggestions": ["Keep coverage high."],
            "coverage_assessment": "Coverage passed.",
            "security_assessment": "Security passed.",
            "technical_debt_assessment": "Technical debt passed.",
        },
    )

    run = _execute(run_id)

    assert run["status"] == "completed"
    assert run["decision"] == "pass"
    assert run["score"] == 91
    assert run["ai_review_json"]["status"] == "generated"
    assert run["ai_review_json"]["summary"] == "The PR passes all configured gates."
    assert "**Score:** 91/100" in run["final_report_markdown"]


def test_execute_pending_run_completes_with_fail_when_any_gate_fails(
    repository, monkeypatch
):
    run_id = _create_run(repository)

    from app.models.enums import FindingCategory
    from app.services.gates import coverage_gate, security_gate, technical_debt_gate

    monkeypatch.setattr(
        coverage_gate,
        "run_coverage_gate",
        lambda **kwargs: _gate_result("fail", FindingCategory.COVERAGE),
    )
    monkeypatch.setattr(
        security_gate,
        "run_security_gate",
        lambda **kwargs: _gate_result("pass", FindingCategory.SECURITY),
    )
    monkeypatch.setattr(
        technical_debt_gate,
        "run_technical_debt_gate",
        lambda **kwargs: _gate_result("pass", FindingCategory.TECHNICAL_DEBT),
    )

    run = _execute(run_id)

    assert run["status"] == "completed"
    assert run["decision"] == "fail"
    assert run["score"] is None
    assert run["ai_review_json"]["status"] == "skipped"
    assert run["coverage_result_json"]["status"] == "fail"
    assert len(run["findings"]) == 1
    assert "# AI Quality Gate: FAIL" in run["final_report_markdown"]


def test_execute_pending_run_errors_and_keeps_partial_snapshots(
    repository, monkeypatch
):
    run_id = _create_run(repository)

    from app.services.agent import quality_agent
    from app.services.gates import coverage_gate, security_gate, technical_debt_gate
    from app.services.gates.types import GateResult

    monkeypatch.setattr(
        coverage_gate,
        "run_coverage_gate",
        lambda **kwargs: _gate_result("pass", FindingCategory.COVERAGE),
    )
    monkeypatch.setattr(
        security_gate,
        "run_security_gate",
        lambda **kwargs: GateResult(
            snapshot={"status": "error"},
            findings=[],
            error_message="semgrep output was empty",
        ),
    )
    monkeypatch.setattr(
        technical_debt_gate,
        "run_technical_debt_gate",
        lambda **kwargs: _gate_result("pass", FindingCategory.TECHNICAL_DEBT),
    )
    ai_called = False

    def fake_ai_review(**kwargs):
        nonlocal ai_called
        ai_called = True
        return {"status": "generated", "score": 80}

    monkeypatch.setattr(quality_agent, "generate_ai_review_snapshot", fake_ai_review)

    run = _execute(run_id)

    assert run["status"] == "error"
    assert run["decision"] is None
    assert run["coverage_result_json"]["status"] == "pass"
    assert run["security_result_json"]["status"] == "error"
    assert run["technical_debt_result_json"] == {}
    assert run["error_message"] == "semgrep output was empty"
    assert run["ai_review_json"] == {}
    assert "# AI Quality Gate: OPERATIONAL ERROR" in run["final_report_markdown"]
    assert ai_called is False


def test_execute_skips_disabled_gates(repository, monkeypatch):
    run_id = _create_run(repository)

    from app.models.quality_gate_config import QualityGateConfig
    from app.services.gates import coverage_gate, security_gate, technical_debt_gate

    with SessionLocal() as db:
        config = (
            db.query(QualityGateConfig)
            .filter_by(repository_id=repository["id"])
            .one()
        )
        config.coverage_enabled = False
        config.security_enabled = False
        db.commit()

    def disabled_gate_called(**kwargs):
        raise AssertionError("disabled gate should not be called")

    monkeypatch.setattr(coverage_gate, "run_coverage_gate", disabled_gate_called)
    monkeypatch.setattr(security_gate, "run_security_gate", disabled_gate_called)
    monkeypatch.setattr(
        technical_debt_gate,
        "run_technical_debt_gate",
        lambda **kwargs: _gate_result("pass", FindingCategory.TECHNICAL_DEBT),
    )

    run = _execute(run_id)

    assert run["status"] == "completed"
    assert run["decision"] == "pass"
    assert run["coverage_result_json"] == {
        "status": "skipped",
        "reason": "coverage_gate_disabled",
    }
    assert run["security_result_json"] == {
        "status": "skipped",
        "reason": "security_gate_disabled",
    }
    assert run["technical_debt_result_json"]["status"] == "pass"


def test_execute_publishes_pending_then_success_with_target_url(
    repository, monkeypatch, github_writes
):
    run_id = _create_run(repository)
    _stub_passing_gates(monkeypatch)

    run = _execute(run_id)
    expected_url = f"http://localhost:5173/analysis-runs/{run_id}"

    assert run["status"] == "completed"
    assert run["decision"] == "pass"
    assert [item["state"] for item in github_writes["status"]] == ["pending", "success"]
    assert github_writes["status"][0]["description"] == "Quality gate running."
    assert github_writes["status"][1]["description"] == "Quality gate passed."
    assert all(item["context"] == "ai-quality-gate" for item in github_writes["status"])
    assert all(item["target_url"] == expected_url for item in github_writes["status"])
    assert github_writes["comments"]
    assert f"<!-- ai-quality-gate:analysis-run:{run_id} -->" in github_writes["comments"][0]["body"]
    assert "required check" not in github_writes["comments"][0]["body"].lower()
    assert "branch protection" not in github_writes["comments"][0]["body"].lower()


def test_execute_publishes_failure_status_when_gate_fails(
    repository, monkeypatch, github_writes
):
    run_id = _create_run(repository)
    from app.services.gates import coverage_gate, security_gate, technical_debt_gate

    monkeypatch.setattr(
        coverage_gate,
        "run_coverage_gate",
        lambda **kwargs: _gate_result("fail", FindingCategory.COVERAGE),
    )
    monkeypatch.setattr(
        security_gate,
        "run_security_gate",
        lambda **kwargs: _gate_result("pass", FindingCategory.SECURITY),
    )
    monkeypatch.setattr(
        technical_debt_gate,
        "run_technical_debt_gate",
        lambda **kwargs: _gate_result("pass", FindingCategory.TECHNICAL_DEBT),
    )

    run = _execute(run_id)

    assert run["status"] == "completed"
    assert run["decision"] == "fail"
    assert [item["state"] for item in github_writes["status"]] == ["pending", "failure"]


def test_execute_publishes_error_status_on_operational_failure(
    repository, monkeypatch, github_writes
):
    run_id = _create_run(repository)
    from app.services.gates import coverage_gate

    monkeypatch.setattr(
        coverage_gate,
        "run_coverage_gate",
        lambda **kwargs: (_ for _ in ()).throw(RuntimeError("scanner crashed")),
    )

    run = _execute(run_id)

    assert run["status"] == "error"
    assert run["decision"] is None
    assert [item["state"] for item in github_writes["status"]] == ["pending", "error"]
    assert github_writes["comments"]
    assert "OPERATIONAL ERROR" in github_writes["comments"][0]["body"]


def test_execute_updates_existing_github_comment(
    repository, monkeypatch, github_writes
):
    run_id = _create_run(repository)
    _stub_passing_gates(monkeypatch)

    def fake_list(self, owner, name, pr_number):
        return [
            {
                "id": 101,
                "body": f"old\n<!-- ai-quality-gate:analysis-run:{run_id} -->",
            }
        ]

    monkeypatch.setattr(GitHubClient, "list_issue_comments", fake_list)

    run = _execute(run_id)

    assert run["status"] == "completed"
    assert github_writes["comments"] == []
    assert github_writes["comment_updates"][0]["comment_id"] == 101
    assert f"<!-- ai-quality-gate:analysis-run:{run_id} -->" in github_writes[
        "comment_updates"
    ][0]["body"]


def test_github_publish_failure_does_not_change_run_status_or_decision(
    repository, monkeypatch, github_writes
):
    run_id = _create_run(repository)
    _stub_passing_gates(monkeypatch)

    def boom(self, *args, **kwargs):
        raise AppError(502, "github_request_failed", "GitHub API request failed.")

    monkeypatch.setattr(GitHubClient, "create_commit_status", boom)
    monkeypatch.setattr(GitHubClient, "create_issue_comment", boom)

    run = _execute(run_id)

    assert run["status"] == "completed"
    assert run["decision"] == "pass"
    with SessionLocal() as db:
        persisted = db.get(AnalysisRun, UUID(run_id))
        assert persisted.status == AnalysisRunStatus.COMPLETED
        assert persisted.decision.value == "pass"


def test_disabled_publication_flags_skip_github_writes(
    repository, monkeypatch, github_writes
):
    run_id = _create_run(repository)
    _set_publish_flags(repository["id"], comment=False, status=False)
    _stub_passing_gates(monkeypatch)

    run = _execute(run_id)

    assert run["status"] == "completed"
    assert run["decision"] == "pass"
    assert github_writes["status"] == []
    assert github_writes["comments"] == []
    assert github_writes["comment_updates"] == []
