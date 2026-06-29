from datetime import UTC, datetime

from app.db.session import SessionLocal
from app.models.analysis_run import AnalysisRun
from app.models.enums import AnalysisRunStatus, AnalysisTriggerSource, FindingCategory


def _create_run(
    repository,
    *,
    diff_snapshot="diff --git",
    status=AnalysisRunStatus.PENDING,
):
    with SessionLocal() as db:
        run = AnalysisRun(
            repository_id=repository["id"],
            pr_number=42,
            head_sha="head123",
            status=status,
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


def test_execute_rejects_non_pending_run(client, repository):
    run_id = _create_run(repository, status=AnalysisRunStatus.COMPLETED)

    response = client.post(f"/api/analysis-runs/{run_id}/execute")

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "analysis_run_not_pending"


def test_execute_pending_run_completes_with_pass(client, repository, monkeypatch):
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

    response = client.post(f"/api/analysis-runs/{run_id}/execute")

    assert response.status_code == 200
    run = response.json()
    assert run["status"] == "completed"
    assert run["decision"] == "pass"
    assert run["score"] is None
    assert run["ai_review_json"]["status"] == "skipped"
    assert run["started_at"] is not None
    assert run["finished_at"] is not None
    assert "# AI Quality Gate: PASS" in run["final_report_markdown"]


def test_execute_pending_run_stores_generated_ai_review_and_score(
    client, repository, monkeypatch
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

    response = client.post(f"/api/analysis-runs/{run_id}/execute")

    assert response.status_code == 200
    run = response.json()
    assert run["status"] == "completed"
    assert run["decision"] == "pass"
    assert run["score"] == 91
    assert run["ai_review_json"]["status"] == "generated"
    assert run["ai_review_json"]["summary"] == "The PR passes all configured gates."
    assert "**Score:** 91/100" in run["final_report_markdown"]


def test_execute_pending_run_completes_with_fail_when_any_gate_fails(
    client, repository, monkeypatch
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

    response = client.post(f"/api/analysis-runs/{run_id}/execute")

    assert response.status_code == 200
    run = response.json()
    assert run["status"] == "completed"
    assert run["decision"] == "fail"
    assert run["score"] is None
    assert run["ai_review_json"]["status"] == "skipped"
    assert run["coverage_result_json"]["status"] == "fail"
    assert len(run["findings"]) == 1
    assert "# AI Quality Gate: FAIL" in run["final_report_markdown"]


def test_execute_pending_run_errors_and_keeps_partial_snapshots(
    client, repository, monkeypatch
):
    run_id = _create_run(repository)

    from app.models.enums import FindingCategory
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

    response = client.post(f"/api/analysis-runs/{run_id}/execute")

    assert response.status_code == 200
    run = response.json()
    assert run["status"] == "error"
    assert run["decision"] is None
    assert run["coverage_result_json"]["status"] == "pass"
    assert run["security_result_json"]["status"] == "error"
    assert run["technical_debt_result_json"] == {}
    assert run["error_message"] == "semgrep output was empty"
    assert run["ai_review_json"] == {}
    assert "# AI Quality Gate: OPERATIONAL ERROR" in run["final_report_markdown"]
    assert ai_called is False
