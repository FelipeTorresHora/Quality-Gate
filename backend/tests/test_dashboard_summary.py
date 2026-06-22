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
    passing = client.post(
        f"/api/repositories/{repository['id']}/analysis-runs/mock",
        json={"scenario": "passing", "pr_number": 1, "head_sha": "sha-pass"},
    ).json()
    failing = client.post(
        f"/api/repositories/{repository['id']}/analysis-runs/mock",
        json={"scenario": "security_fail", "pr_number": 2, "head_sha": "sha-fail"},
    ).json()
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
        passing["id"],
        failing["id"],
    }
    assert summary["recent_analysis_runs"][0]["repository_full_name"] == (
        "horinha04/meu-projeto"
    )


def test_dashboard_summary_calculates_approval_rate_for_completed_decided_runs(
    client, repository
):
    client.post(
        f"/api/repositories/{repository['id']}/analysis-runs/mock",
        json={"scenario": "passing", "pr_number": 1, "head_sha": "sha-pass-1"},
    )
    client.post(
        f"/api/repositories/{repository['id']}/analysis-runs/mock",
        json={"scenario": "passing", "pr_number": 2, "head_sha": "sha-pass-2"},
    )
    client.post(
        f"/api/repositories/{repository['id']}/analysis-runs/mock",
        json={"scenario": "coverage_fail", "pr_number": 3, "head_sha": "sha-fail"},
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
    client.post(
        f"/api/repositories/{repository['id']}/analysis-runs/mock",
        json={"scenario": "mixed_fail", "pr_number": 1, "head_sha": "sha-mixed"},
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
    client.post(
        f"/api/repositories/{repository['id']}/analysis-runs/mock",
        json={"scenario": "mixed_fail", "pr_number": 1, "head_sha": "sha-mixed"},
    )
    run = client.post(
        f"/api/repositories/{repository['id']}/analysis-runs/mock",
        json={"scenario": "security_fail", "pr_number": 2, "head_sha": "sha-security"},
    ).json()
    _insert_finding(run["id"], FindingCategory.SECURITY, FindingSeverity.MEDIUM)

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
) -> None:
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
            pull_request_snapshot_json={},
            changed_files_snapshot_json=[],
            diff_truncated=False,
        )
        db.add(run)
        db.commit()


def _insert_finding(
    analysis_run_id: str,
    category: FindingCategory,
    severity: FindingSeverity,
) -> None:
    with SessionLocal() as db:
        finding = AnalysisFinding(
            analysis_run_id=UUID(analysis_run_id),
            category=category,
            severity=severity,
            file_path="src/example.py",
            line_number=10,
            title="Extra blocking finding",
            description="Additional test finding.",
            blocking=True,
        )
        db.add(finding)
        db.commit()
