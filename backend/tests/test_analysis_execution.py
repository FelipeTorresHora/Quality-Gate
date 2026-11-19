from uuid import UUID

import pytest

from app.core.errors import AppError
from app.db.session import SessionLocal
from app.models.analysis_run import AnalysisRun
from app.models.enums import (
    AnalysisRunStatus,
    AnalysisTriggerSource,
    FindingCategory,
    FindingSeverity,
    FindingSource,
    GateDecision,
    GateEvaluationMode,
)
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
    assert "quality-gate fail" in run["final_report_markdown"]
    assert "not an operational error" in run["final_report_markdown"]


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
    assert "not** a quality-gate fail" in run["final_report_markdown"]
    assert "**Gate Decision:** none" in run["final_report_markdown"]
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


def test_ai_finding_payloads_drop_malformed_rows():
    comment = analysis_execution_service._ai_comment_payload
    finding = analysis_execution_service._ai_finding_payload

    assert comment("nope") is None
    assert comment({"title": " ", "body": "body", "file_path": "a.py"}) is None
    assert comment({"title": "Title", "body": " ", "file_path": "a.py"}) is None
    assert comment({"title": "Title", "body": "body", "file_path": ""}) is None
    assert comment(
        {"title": "Title", "body": "body", "file_path": "a.py", "severity": "nope"}
    ) is None
    kept = comment(
        {
            "title": " Title ",
            "body": " body ",
            "file_path": "a.py",
            "severity": FindingSeverity.LOW,
            "line_number": True,
            "confidence": 2,
            "suggestion_code": "  ",
        }
    )
    assert kept["severity"] == FindingSeverity.LOW
    assert kept["line_number"] is None
    assert kept["confidence"] is None
    assert kept["suggestion_code"] is None

    assert finding(None, "coverage") is None
    assert finding(
        {
            "title": " ",
            "description": "text",
            "category": "coverage",
            "severity": "low",
        },
        "coverage",
    ) is None
    assert finding(
        {"title": "Title", "description": None, "category": "coverage", "severity": "low"},
        "coverage",
    ) is None
    assert finding(
        {"title": "Title", "description": "text", "category": "nope", "severity": "low"},
        "coverage",
    ) is None
    assert finding(
        {
            "title": "Title",
            "description": "text",
            "category": "security",
            "severity": "low",
        },
        "coverage",
    ) is None
    assert finding(
        {
            "title": "Title",
            "description": "text",
            "category": "coverage",
            "severity": "nope",
        },
        "coverage",
    ) is None
    payload = finding(
        {
            "title": " Title ",
            "description": "text",
            "category": FindingCategory.COVERAGE,
            "severity": FindingSeverity.MEDIUM,
            "file_path": 5,
            "line_number": 0,
            "confidence": True,
            "suggestion_code": "",
        },
        "coverage",
    )
    assert payload["category"] == FindingCategory.COVERAGE
    assert payload["file_path"] is None
    assert payload["line_number"] is None
    assert payload["confidence"] is None
    assert payload["suggestion_code"] is None


def test_accepted_score_keeps_generated_and_partial_numbers():
    accept = analysis_execution_service._accepted_score

    assert accept({"status": "generated", "score": 91}) == 91.0
    assert accept({"status": "partial", "score": 0}) == 0.0
    assert accept({"status": "partial", "score": 100}) == 100.0
    assert accept({"status": "partial", "score": None}) is None
    assert accept({"status": "generated", "score": True}) is None
    assert accept({"status": "generated", "score": "91"}) is None
    assert accept({"status": "generated", "score": 101}) is None
    assert accept({"status": "generated", "score": -1}) is None
    assert accept({"status": "skipped", "score": 90}) is None
    assert accept({"status": "error", "score": 90}) is None


def test_hybrid_deterministic_and_ai_only_follow_pillar_modes(repository, monkeypatch):
    run_id = _create_run(repository)
    _set_modes(
        repository["id"],
        coverage_mode=GateEvaluationMode.HYBRID,
        security_mode=GateEvaluationMode.DETERMINISTIC,
        technical_debt_mode=GateEvaluationMode.AI_ONLY,
    )
    containers = _record_container_gates(monkeypatch)
    schemas = _install_fake_review_model(monkeypatch)
    entered = _record_workspace(monkeypatch)

    run = _execute(run_id)

    assert containers == ["coverage", "security"]
    assert entered["count"] == 1
    assert "AICoverageReview" in schemas
    assert "AITechDebtReview" in schemas
    assert "AISecurityReview" not in schemas
    assert "ReviewSynthesis" in schemas
    assert run["status"] == "completed"
    assert run["decision"] == "pass"
    assert run["score"] == 88
    assert run["coverage_result_json"]["status"] == "pass"
    assert run["security_result_json"]["status"] == "pass"
    assert run["technical_debt_result_json"] == {
        "status": "skipped",
        "reason": "technical_debt_mode_ai_only",
    }
    stored = _finding_rows(run_id)
    ai_rows = [row for row in stored if row["source"] == FindingSource.AI.value]
    assert {row["category"] for row in ai_rows} == {
        FindingCategory.COVERAGE.value,
        FindingCategory.TECHNICAL_DEBT.value,
    }
    assert ai_rows
    assert all(row["blocking"] is False for row in ai_rows)
    assert not any(row["source"] == FindingSource.DETERMINISTIC.value for row in stored)


def test_ai_only_skips_container_checkout(repository, monkeypatch):
    run_id = _create_run(repository)
    _set_modes(
        repository["id"],
        coverage_mode=GateEvaluationMode.AI_ONLY,
        security_mode=GateEvaluationMode.AI_ONLY,
        technical_debt_mode=GateEvaluationMode.AI_ONLY,
    )
    containers = _record_container_gates(monkeypatch)
    schemas = _install_fake_review_model(monkeypatch)

    def workspace_forbidden(*args, **kwargs):
        raise AssertionError("checkout prep should be skipped")

    monkeypatch.setattr(
        analysis_execution_service,
        "GateExecutionEvidenceWorkspace",
        workspace_forbidden,
    )

    run = _execute(run_id)

    assert containers == []
    assert "AICoverageReview" in schemas
    assert "AISecurityReview" in schemas
    assert "AITechDebtReview" in schemas
    assert run["status"] == "completed"
    assert run["decision"] == "pass"
    assert run["coverage_result_json"]["reason"] == "coverage_mode_ai_only"
    assert run["security_result_json"]["reason"] == "security_mode_ai_only"
    assert run["technical_debt_result_json"]["reason"] == "technical_debt_mode_ai_only"
    assert all(
        row["source"] == FindingSource.AI.value and row["blocking"] is False
        for row in _finding_rows(run_id)
    )


def test_ai_findings_persist_for_partial_review_without_changing_decision(
    repository, monkeypatch
):
    run_id = _create_run(repository)

    from app.services.gates import coverage_gate

    monkeypatch.setattr(
        coverage_gate,
        "run_coverage_gate",
        lambda **kwargs: _gate_result("fail", FindingCategory.COVERAGE),
    )
    _stub_passing_gates_except_coverage(monkeypatch)
    seen = {}

    def fake_review(**kwargs):
        with SessionLocal() as db:
            stored = db.get(AnalysisRun, UUID(run_id))
            seen["decision"] = stored.decision
            seen["coverage"] = stored.coverage_result_json["status"]
        return _partial_snapshot()

    from app.services.agent import quality_agent

    monkeypatch.setattr(quality_agent, "generate_ai_review_snapshot", fake_review)

    run = _execute(run_id)
    rows = _finding_rows(run_id)
    ai_rows = [row for row in rows if row["source"] == FindingSource.AI.value]

    assert seen == {"decision": GateDecision.FAIL, "coverage": "fail"}
    assert run["status"] == "completed"
    assert run["decision"] == "fail"
    assert run["score"] == 73
    assert run["ai_review_json"]["status"] == "partial"
    assert run["ai_review_json"]["reason"] == "context_budget_exhausted"
    assert {row["category"] for row in ai_rows} == {
        FindingCategory.CODE_REVIEW.value,
        FindingCategory.COVERAGE.value,
        FindingCategory.TECHNICAL_DEBT.value,
    }
    assert all(row["blocking"] is False for row in ai_rows)
    coverage = next(row for row in ai_rows if row["title"] == "Uncovered branch")
    assert coverage["confidence"] == 0.4
    assert coverage["suggestion_code"] == "add a test"
    comment = next(row for row in ai_rows if row["category"] == "code_review")
    assert comment["line_number"] == 4
    assert any(
        row["source"] == FindingSource.DETERMINISTIC.value and row["blocking"] is True
        for row in rows
    )


def test_ai_review_failure_keeps_deterministic_results(repository, monkeypatch):
    run_id = _create_run(repository)
    _stub_passing_gates(monkeypatch)

    def explode(**kwargs):
        raise RuntimeError("llm down")

    from app.services.agent import quality_agent

    monkeypatch.setattr(quality_agent, "generate_ai_review_snapshot", explode)

    run = _execute(run_id)

    assert run["status"] == "completed"
    assert run["decision"] == "pass"
    assert run["score"] is None
    assert run["coverage_result_json"]["status"] == "pass"
    assert run["security_result_json"]["status"] == "pass"
    assert run["technical_debt_result_json"]["status"] == "pass"
    assert run["ai_review_json"]["status"] == "error"
    assert run["ai_review_json"]["reason"] == "ai_review_failed"
    assert run["findings"] == []


def test_non_dict_ai_snapshot_becomes_an_error_without_findings(
    repository, monkeypatch
):
    run_id = _create_run(repository)
    _stub_passing_gates(monkeypatch)

    from app.services.agent import quality_agent

    monkeypatch.setattr(
        quality_agent,
        "generate_ai_review_snapshot",
        lambda **kwargs: ["not", "a", "snapshot"],
    )

    run = _execute(run_id)

    assert run["status"] == "completed"
    assert run["decision"] == "pass"
    assert run["score"] is None
    assert run["ai_review_json"]["status"] == "error"
    assert _finding_rows(run_id) == []


def test_partial_review_with_unusable_insights_stores_score_only(
    repository, monkeypatch
):
    run_id = _create_run(repository)
    _stub_passing_gates(monkeypatch)

    from app.services.agent import quality_agent

    monkeypatch.setattr(
        quality_agent,
        "generate_ai_review_snapshot",
        lambda **kwargs: {
            "status": "partial",
            "score": 10,
            "summary": "Partial.",
            "inline_comments": ["nope", {"title": " ", "body": "x", "file_path": "a.py"}],
            "pillar_insights": [],
            "reason": "context_budget_exhausted",
        },
    )

    run = _execute(run_id)

    assert run["decision"] == "pass"
    assert run["score"] == 10
    assert all(row["source"] == FindingSource.DETERMINISTIC.value for row in _finding_rows(run_id))


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


def _set_modes(repository_id, **modes):
    with SessionLocal() as db:
        config = (
            db.query(QualityGateConfig).filter_by(repository_id=repository_id).one()
        )
        for name, value in modes.items():
            setattr(config, name, value)
        db.commit()


def _record_container_gates(monkeypatch):
    calls = []

    def wrap(name, category):
        def inner(**kwargs):
            calls.append(name)
            return _gate_result("pass", category)

        return inner

    from app.services.gates import coverage_gate, security_gate, technical_debt_gate

    monkeypatch.setattr(
        coverage_gate,
        "run_coverage_gate",
        wrap("coverage", FindingCategory.COVERAGE),
    )
    monkeypatch.setattr(
        security_gate,
        "run_security_gate",
        wrap("security", FindingCategory.SECURITY),
    )
    monkeypatch.setattr(
        technical_debt_gate,
        "run_technical_debt_gate",
        wrap("technical_debt", FindingCategory.TECHNICAL_DEBT),
    )
    return calls


def _stub_passing_gates_except_coverage(monkeypatch):
    from app.services.gates import security_gate, technical_debt_gate

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


def _record_workspace(monkeypatch):
    entered = {"count": 0}
    original = analysis_execution_service.GateExecutionEvidenceWorkspace

    class RecordingWorkspace:
        def __init__(self, *args, **kwargs):
            entered["count"] += 1
            self._inner = original(*args, **kwargs)

        def __enter__(self):
            return self._inner.__enter__()

        def __exit__(self, exc_type, exc, traceback):
            return self._inner.__exit__(exc_type, exc, traceback)

    monkeypatch.setattr(
        analysis_execution_service,
        "GateExecutionEvidenceWorkspace",
        RecordingWorkspace,
    )
    return entered


def _install_fake_review_model(monkeypatch):
    from app.core.config import Settings
    from app.services.agent import graph as graph_module
    from app.services.agent import quality_agent
    from app.services.agent.nodes.synthesize import ReviewSynthesis
    from app.services.agent.schemas import (
        AICoverageReview,
        AIGateFinding,
        AISecurityReview,
        AITechDebtReview,
        BatchReviewOutput,
    )

    seen = []

    def finding(category):
        return AIGateFinding(
            category=category,
            severity=FindingSeverity.MEDIUM,
            title=f"{category.value} note",
            description="Non-blocking AI note.",
            confidence=0.6,
        )

    def fake_structured(llm, schema, messages):
        seen.append(schema.__name__)
        if schema is AICoverageReview:
            return AICoverageReview(
                summary="Coverage reviewed.",
                coverage_assessment="Changed lines need a test.",
                findings=[finding(FindingCategory.COVERAGE)],
            )
        if schema is AISecurityReview:
            return AISecurityReview(
                summary="Security reviewed.",
                security_assessment="No confirmed issue.",
                findings=[finding(FindingCategory.SECURITY)],
            )
        if schema is AITechDebtReview:
            return AITechDebtReview(
                summary="Debt reviewed.",
                technical_debt_assessment="Complexity is fine.",
                findings=[finding(FindingCategory.TECHNICAL_DEBT)],
            )
        if schema is BatchReviewOutput:
            return BatchReviewOutput(batch_id="batch-1", summary="No comments.")
        if schema is ReviewSynthesis:
            return ReviewSynthesis(
                score=88,
                summary="Mixed review.",
                risk_level="low",
                coverage_assessment="Coverage reviewed.",
                security_assessment="Security stayed deterministic.",
                technical_debt_assessment="Debt reviewed.",
            )
        raise AssertionError(schema.__name__)

    for module_name in (
        "app.services.agent.nodes",
        "app.services.agent.nodes.synthesize",
        "app.services.agent.nodes.review_batch",
    ):
        monkeypatch.setattr(f"{module_name}.call_structured", fake_structured)
        monkeypatch.setattr(f"{module_name}.build_chat_model", lambda: object())
    monkeypatch.setattr(
        quality_agent,
        "get_settings",
        lambda: Settings(openai_api_key="sk-test", langsmith_tracing=False),
    )
    graph_module.compiled_review_graph.cache_clear()
    return seen


def _finding_rows(run_id):
    from app.models.analysis_finding import AnalysisFinding

    with SessionLocal() as db:
        rows = (
            db.query(AnalysisFinding)
            .filter_by(analysis_run_id=UUID(run_id))
            .order_by(AnalysisFinding.created_at, AnalysisFinding.title)
            .all()
        )
        return [
            {
                "category": row.category.value,
                "source": row.source.value,
                "blocking": row.blocking,
                "title": row.title,
                "confidence": row.confidence,
                "suggestion_code": row.suggestion_code,
                "line_number": row.line_number,
            }
            for row in rows
        ]


def _partial_snapshot():
    from app.services.agent.schemas import (
        AICoverageReview,
        AIGateFinding,
        AIReviewPartial,
        AITechDebtReview,
        ContextBudgetMetadata,
        InlineComment,
        PillarInsights,
    )

    payload = AIReviewPartial(
        score=73,
        summary="The context budget stopped the review early.",
        coverage_assessment="Coverage failed its policy.",
        security_assessment="",
        technical_debt_assessment="Debt is fine.",
        inline_comments=[
            InlineComment(
                file_path="src/app.py",
                line_number=4,
                title="Name the flag",
                body="Rename the flag so the branch is obvious.",
                severity=FindingSeverity.MEDIUM,
                confidence=0.8,
            )
        ],
        pillar_insights=PillarInsights(
            coverage=AICoverageReview(
                summary="Coverage is below the policy.",
                coverage_assessment="Changed lines are uncovered.",
                findings=[
                    AIGateFinding(
                        category=FindingCategory.COVERAGE,
                        severity=FindingSeverity.HIGH,
                        file_path="src/app.py",
                        line_number=4,
                        title="Uncovered branch",
                        description="This branch has no test.",
                        confidence=0.4,
                        suggestion_code="add a test",
                    )
                ],
            ),
            security=None,
            technical_debt=AITechDebtReview(
                summary="No new debt.",
                technical_debt_assessment="Functions stay small.",
                findings=[
                    AIGateFinding(
                        category=FindingCategory.TECHNICAL_DEBT,
                        severity=FindingSeverity.LOW,
                        title="Optional rename",
                        description="A shorter name would help.",
                        confidence=0.2,
                    )
                ],
            ),
        ),
        context_budget=ContextBudgetMetadata(
            batches_sent=1,
            batches_total=2,
            review_truncated=True,
            skipped_files=["generated.lock"],
        ),
    ).model_dump(mode="json")
    payload["inline_comments"].extend(
        [
            "nope",
            {
                "file_path": "src/app.py",
                "line_number": True,
                "title": " ",
                "body": "missing title",
                "severity": "medium",
            },
            {
                "file_path": "",
                "line_number": 2,
                "title": "No path",
                "body": "skipped",
                "severity": "low",
            },
        ]
    )
    payload["pillar_insights"]["coverage"]["findings"].extend(
        [
            None,
            {
                "category": "security",
                "severity": "low",
                "title": "Wrong pillar",
                "description": "dropped",
            },
            {
                "category": FindingCategory.COVERAGE,
                "severity": "low",
                "title": "Enum category",
                "description": "kept from an enum value",
                "confidence": 2,
                "suggestion_code": "",
                "file_path": 5,
                "line_number": 0,
            },
        ]
    )
    debt = payload["pillar_insights"]["technical_debt"]["findings"][0]
    debt["confidence"] = True
    debt["suggestion_code"] = "  "
    debt["file_path"] = 5
    payload["pillar_insights"]["technical_debt"]["findings"].append(
        {
            "category": "technical_debt",
            "severity": "nope",
            "title": "Bad severity",
            "description": "dropped",
        }
    )
    return payload
