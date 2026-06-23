from uuid import UUID

from app.db.session import SessionLocal
from app.models.analysis_finding import AnalysisFinding
from app.models.analysis_run import AnalysisRun
from app.models.enums import (
    AnalysisRunStatus,
    AnalysisTriggerSource,
    FindingCategory,
    FindingSeverity,
    GateDecision,
)


def test_dashboard_summary_with_no_data(client, reset_database):
    response = client.get("/api/dashboard/summary")

    assert response.status_code == 200
    assert response.json() == {
        "total_repositories": 0,
        "total_analysis_runs": 0,
        "run_status_counts": {
            "pending": 0,
            "running": 0,
            "completed": 0,
            "error": 0,
        },
        "gate_decision_counts": {"pass": 0, "fail": 0},
        "approval_rate": None,
        "recent_analysis_runs": [],
        "finding_counts": [],
        "top_blocking_categories": [],
    }


def test_dashboard_summary_counts_run_statuses_and_gate_decisions(
    client, repository
):
    passing = _insert_run(
        repository["id"],
        1,
        "sha-pass",
        AnalysisRunStatus.COMPLETED,
        decision=GateDecision.PASS,
    )
    failing = _insert_run(
        repository["id"],
        2,
        "sha-fail",
        AnalysisRunStatus.COMPLETED,
        decision=GateDecision.FAIL,
    )
    _insert_run(repository["id"], 3, "sha-pending", AnalysisRunStatus.PENDING)
    _insert_run(repository["id"], 4, "sha-running", AnalysisRunStatus.RUNNING)
    _insert_run(repository["id"], 5, "sha-error", AnalysisRunStatus.ERROR)

    response = client.get("/api/dashboard/summary")

    assert response.status_code == 200
    summary = response.json()
    assert summary["total_repositories"] == 1
    assert summary["total_analysis_runs"] == 5
    assert summary["run_status_counts"] == {
        "pending": 1,
        "running": 1,
        "completed": 2,
        "error": 1,
    }
    assert summary["gate_decision_counts"] == {"pass": 1, "fail": 1}
    assert {run["id"] for run in summary["recent_analysis_runs"]} >= {
        passing,
        failing,
    }
    assert summary["recent_analysis_runs"][0]["repository_full_name"] == (
        "horinha04/meu-projeto"
    )


def test_dashboard_summary_calculates_approval_rate_for_completed_decided_runs(
    client, repository
):
    _insert_run(
        repository["id"],
        1,
        "sha-pass-1",
        AnalysisRunStatus.COMPLETED,
        decision=GateDecision.PASS,
    )
    _insert_run(
        repository["id"],
        2,
        "sha-pass-2",
        AnalysisRunStatus.COMPLETED,
        decision=GateDecision.PASS,
    )
    _insert_run(
        repository["id"],
        3,
        "sha-fail",
        AnalysisRunStatus.COMPLETED,
        decision=GateDecision.FAIL,
    )
    _insert_run(repository["id"], 4, "sha-completed-none", AnalysisRunStatus.COMPLETED)
    _insert_run(
        repository["id"],
        5,
        "sha-pending-pass",
        AnalysisRunStatus.PENDING,
        decision=GateDecision.PASS,
    )

    response = client.get("/api/dashboard/summary")

    assert response.status_code == 200
    assert response.json()["approval_rate"] == 66.7


def test_dashboard_summary_aggregates_findings_by_category_and_severity(
    client, repository
):
    _insert_run(
        repository["id"],
        1,
        "sha-mixed",
        AnalysisRunStatus.COMPLETED,
        decision=GateDecision.FAIL,
        findings=[
            (FindingCategory.COVERAGE, FindingSeverity.HIGH, True),
            (FindingCategory.SECURITY, FindingSeverity.CRITICAL, True),
            (FindingCategory.TECHNICAL_DEBT, FindingSeverity.MEDIUM, False),
        ],
    )

    response = client.get("/api/dashboard/summary")

    assert response.status_code == 200
    counts = {
        (item["category"], item["severity"]): item["count"]
        for item in response.json()["finding_counts"]
    }
    assert counts == {
        ("coverage", "high"): 1,
        ("security", "critical"): 1,
        ("technical_debt", "medium"): 1,
    }


def test_dashboard_summary_reports_top_blocking_categories(client, repository):
    _insert_run(
        repository["id"],
        1,
        "sha-mixed",
        AnalysisRunStatus.COMPLETED,
        decision=GateDecision.FAIL,
        findings=[
            (FindingCategory.COVERAGE, FindingSeverity.HIGH, True),
            (FindingCategory.SECURITY, FindingSeverity.CRITICAL, True),
            (FindingCategory.TECHNICAL_DEBT, FindingSeverity.MEDIUM, False),
        ],
    )
    _insert_run(
        repository["id"],
        2,
        "sha-security",
        AnalysisRunStatus.COMPLETED,
        decision=GateDecision.FAIL,
        findings=[
            (FindingCategory.SECURITY, FindingSeverity.HIGH, True),
            (FindingCategory.SECURITY, FindingSeverity.MEDIUM, True),
        ],
    )

    response = client.get("/api/dashboard/summary")

    assert response.status_code == 200
    assert response.json()["top_blocking_categories"] == [
        {"category": "security", "count": 3},
        {"category": "coverage", "count": 1},
    ]


def _insert_run(
    repository_id: str,
    pr_number: int,
    head_sha: str,
    status: AnalysisRunStatus,
    decision: GateDecision | None = None,
    findings: list[tuple[FindingCategory, FindingSeverity, bool]] | None = None,
) -> str:
    with SessionLocal() as db:
        run = AnalysisRun(
            repository_id=UUID(repository_id),
            pr_number=pr_number,
            head_sha=head_sha,
            status=status,
            decision=decision,
            trigger_source=AnalysisTriggerSource.MANUAL,
            coverage_result_json={},
            security_result_json={},
            technical_debt_result_json={},
            ai_review_json={},
            pull_request_snapshot_json={},
            changed_files_snapshot_json=[],
            diff_truncated=False,
        )
        for index, (category, severity, blocking) in enumerate(findings or [], start=1):
            run.findings.append(
                AnalysisFinding(
                    category=category,
                    severity=severity,
                    file_path="src/example.py",
                    line_number=index,
                    title=f"{category.value} finding {index}",
                    description="Test finding.",
                    blocking=blocking,
                )
            )
        db.add(run)
        db.commit()
        return str(run.id)
