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


def test_dashboard_summary_requires_authentication(client, monkeypatch):
    monkeypatch.setattr(
        "app.services.dashboard_service.get_dashboard_summary",
        lambda db, user: {
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
            "open_pull_requests_needing_action": [],
        },
    )

    response = client.get("/api/dashboard/summary")

    assert response.status_code == 401


def test_dashboard_summary_with_no_data(client, db_session):
    from app.models.user import User
    from app.services import session_service

    user = User(github_user_id=404, github_login="empty-user")
    db_session.add(user)
    db_session.commit()
    created = session_service.create_session(db_session, user)
    client.cookies.set("qg_session", created.cookie_value)

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
        "open_pull_requests_needing_action": [],
    }


def test_dashboard_summary_cache_hit_skips_service(client, repository, monkeypatch):
    cached = {
        "total_repositories": 7,
        "total_analysis_runs": 11,
        "run_status_counts": {
            "pending": 0,
            "running": 0,
            "completed": 11,
            "error": 0,
        },
        "gate_decision_counts": {"pass": 10, "fail": 1},
        "approval_rate": 90.9,
        "recent_analysis_runs": [],
        "finding_counts": [],
        "top_blocking_categories": [],
        "open_pull_requests_needing_action": [],
    }
    monkeypatch.setattr(
        "app.api.routes_dashboard.runtime_cache_service.get_json",
        lambda key: cached,
    )
    monkeypatch.setattr(
        "app.services.dashboard_service.get_dashboard_summary",
        lambda db, user: (_ for _ in ()).throw(AssertionError("cache miss")),
    )

    response = client.get("/api/dashboard/summary")

    assert response.status_code == 200
    assert response.json() == cached


def test_dashboard_summary_cache_miss_stores_payload(
    client, repository, monkeypatch
):
    writes = []
    monkeypatch.setattr(
        "app.api.routes_dashboard.runtime_cache_service.get_json",
        lambda key: None,
    )
    monkeypatch.setattr(
        "app.api.routes_dashboard.runtime_cache_service.set_json",
        lambda key, value, ttl, tags: writes.append(
            {"key": key, "value": value, "ttl": ttl, "tags": tags}
        ),
    )

    response = client.get("/api/dashboard/summary")

    assert response.status_code == 200
    assert writes
    assert writes[0]["key"].startswith("dashboard-summary:v2:user:")
    assert writes[0]["ttl"] == 60
    assert "dashboard-summary" in writes[0]["tags"]
    assert writes[0]["value"] == response.json()


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


def test_dashboard_summary_lists_open_failing_pull_request(
    client, repository, monkeypatch
):
    _enable_github_publication(repository["id"])
    _patch_open_pull_requests(monkeypatch, [_open_pull_request(2, "sha-fail")])
    run_id = _insert_run(
        repository["id"],
        2,
        "sha-fail",
        AnalysisRunStatus.COMPLETED,
        decision=GateDecision.FAIL,
        snapshot={"html_url": "https://github.com/horinha04/meu-projeto/pull/2"},
    )

    response = client.get("/api/dashboard/summary")

    assert response.status_code == 200
    queue = response.json()["open_pull_requests_needing_action"]
    assert len(queue) == 1
    item = queue[0]
    assert item["repository_full_name"] == "horinha04/meu-projeto"
    assert item["pr_number"] == 2
    assert item["pr_title"] == "Fix coverage"
    assert item["html_url"] == "https://github.com/horinha04/meu-projeto/pull/2"
    assert item["head_sha"] == "sha-fail"
    assert item["analysis_run_id"] == run_id
    assert item["status"] == "completed"
    assert item["decision"] == "fail"
    assert item["review_state"] == "current"
    assert item["action"] == "fail"


def test_dashboard_summary_lists_open_operational_error_pull_request(
    client, repository, monkeypatch
):
    _patch_open_pull_requests(monkeypatch, [_open_pull_request(5, "sha-error")])
    run_id = _insert_run(
        repository["id"],
        5,
        "sha-error",
        AnalysisRunStatus.ERROR,
    )

    response = client.get("/api/dashboard/summary")

    assert response.status_code == 200
    item = response.json()["open_pull_requests_needing_action"][0]
    assert item["analysis_run_id"] == run_id
    assert item["status"] == "error"
    assert item["decision"] is None
    assert item["review_state"] == "current"
    assert item["action"] == "error"


def test_dashboard_summary_lists_outdated_open_pull_request(
    client, repository, monkeypatch
):
    _enable_github_publication(repository["id"])
    _patch_open_pull_requests(monkeypatch, [_open_pull_request(8, "sha-new")])
    run_id = _insert_run(
        repository["id"],
        8,
        "sha-old",
        AnalysisRunStatus.COMPLETED,
        decision=GateDecision.PASS,
    )

    response = client.get("/api/dashboard/summary")

    assert response.status_code == 200
    item = response.json()["open_pull_requests_needing_action"][0]
    assert item["analysis_run_id"] == run_id
    assert item["head_sha"] == "sha-new"
    assert item["decision"] == "pass"
    assert item["review_state"] == "outdated"
    assert item["action"] == "outdated"


def test_dashboard_summary_lists_fail_with_publication_disabled(
    client, repository, monkeypatch
):
    _disable_github_publication(repository["id"])
    _patch_open_pull_requests(monkeypatch, [_open_pull_request(3, "sha-fail")])
    _insert_run(
        repository["id"],
        3,
        "sha-fail",
        AnalysisRunStatus.COMPLETED,
        decision=GateDecision.FAIL,
    )

    response = client.get("/api/dashboard/summary")

    assert response.status_code == 200
    item = response.json()["open_pull_requests_needing_action"][0]
    assert item["action"] == "publication_off"
    assert item["comment_on_github"] is False
    assert item["publish_github_status"] is False
    assert item["review_state"] == "current"
    assert item["decision"] == "fail"


def test_dashboard_summary_omits_closed_and_passing_open_pull_requests(
    client, repository, monkeypatch
):
    _enable_github_publication(repository["id"])
    listed_repos = []

    def fake_list_repository_pull_requests(db, repository_id):
        listed_repos.append(str(repository_id))
        return [_open_pull_request(2, "sha-fail")]

    monkeypatch.setattr(
        "app.services.dashboard_service.github_service.list_repository_pull_requests",
        fake_list_repository_pull_requests,
    )
    _insert_run(
        repository["id"],
        1,
        "sha-closed",
        AnalysisRunStatus.COMPLETED,
        decision=GateDecision.FAIL,
    )
    _insert_run(
        repository["id"],
        2,
        "sha-fail",
        AnalysisRunStatus.COMPLETED,
        decision=GateDecision.FAIL,
    )
    _insert_run(
        repository["id"],
        4,
        "sha-pass",
        AnalysisRunStatus.COMPLETED,
        decision=GateDecision.PASS,
    )

    response = client.get("/api/dashboard/summary")

    assert response.status_code == 200
    queue = response.json()["open_pull_requests_needing_action"]
    assert [item["pr_number"] for item in queue] == [2]
    assert listed_repos == [repository["id"]]


def test_dashboard_summary_skips_github_when_no_candidate_runs(
    client, repository, monkeypatch
):
    def fail_list_repository_pull_requests(*args, **kwargs):
        raise AssertionError("GitHub should not be queried without candidate runs")

    monkeypatch.setattr(
        "app.services.dashboard_service.github_service.list_repository_pull_requests",
        fail_list_repository_pull_requests,
    )

    response = client.get("/api/dashboard/summary")

    assert response.status_code == 200
    assert response.json()["open_pull_requests_needing_action"] == []


def test_dashboard_summary_omits_stale_runs_outside_action_window(
    client, repository, monkeypatch
):
    from datetime import UTC, datetime, timedelta

    _enable_github_publication(repository["id"])
    _patch_open_pull_requests(monkeypatch, [_open_pull_request(9, "sha-old")])
    _insert_run(
        repository["id"],
        9,
        "sha-old",
        AnalysisRunStatus.COMPLETED,
        decision=GateDecision.FAIL,
        created_at=datetime.now(UTC) - timedelta(days=15),
    )

    response = client.get("/api/dashboard/summary")

    assert response.status_code == 200
    assert response.json()["open_pull_requests_needing_action"] == []


def test_dashboard_summary_uses_latest_run_per_open_pull_request(
    client, repository, monkeypatch
):
    from datetime import UTC, datetime, timedelta

    _enable_github_publication(repository["id"])
    _patch_open_pull_requests(monkeypatch, [_open_pull_request(11, "sha-new")])
    _insert_run(
        repository["id"],
        11,
        "sha-old",
        AnalysisRunStatus.COMPLETED,
        decision=GateDecision.FAIL,
        created_at=datetime.now(UTC) - timedelta(hours=2),
    )
    latest = _insert_run(
        repository["id"],
        11,
        "sha-new",
        AnalysisRunStatus.COMPLETED,
        decision=GateDecision.FAIL,
        created_at=datetime.now(UTC) - timedelta(hours=1),
    )

    response = client.get("/api/dashboard/summary")

    assert response.status_code == 200
    item = response.json()["open_pull_requests_needing_action"][0]
    assert item["analysis_run_id"] == latest
    assert item["review_state"] == "current"
    assert item["action"] == "fail"


def test_dashboard_summary_survives_github_hydration_failure(
    client, repository, monkeypatch
):
    from app.core.errors import AppError

    _enable_github_publication(repository["id"])
    _insert_run(
        repository["id"],
        2,
        "sha-fail",
        AnalysisRunStatus.COMPLETED,
        decision=GateDecision.FAIL,
    )
    monkeypatch.setattr(
        "app.services.dashboard_service.github_service.list_repository_pull_requests",
        lambda db, repository_id: (_ for _ in ()).throw(
            AppError(502, "github_request_failed", "GitHub API request failed.")
        ),
    )

    response = client.get("/api/dashboard/summary")

    assert response.status_code == 200
    assert response.json()["open_pull_requests_needing_action"] == []
    assert response.json()["total_analysis_runs"] == 1


def _insert_run(
    repository_id: str,
    pr_number: int,
    head_sha: str,
    status: AnalysisRunStatus,
    decision: GateDecision | None = None,
    findings: list[tuple[FindingCategory, FindingSeverity, bool]] | None = None,
    snapshot: dict | None = None,
    created_at=None,
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
            pull_request_snapshot_json=snapshot or {},
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
        db.flush()
        if created_at is not None:
            run.created_at = created_at
        db.commit()
        return str(run.id)


def _enable_github_publication(repository_id: str) -> None:
    _set_github_publication(repository_id, enabled=True)


def _disable_github_publication(repository_id: str) -> None:
    _set_github_publication(repository_id, enabled=False)


def _set_github_publication(repository_id: str, *, enabled: bool) -> None:
    from app.models.quality_gate_config import QualityGateConfig

    with SessionLocal() as db:
        config = (
            db.query(QualityGateConfig)
            .filter(QualityGateConfig.repository_id == UUID(repository_id))
            .one()
        )
        config.comment_on_github = enabled
        config.publish_github_status = enabled
        db.commit()


def _open_pull_request(number: int, head_sha: str):
    from app.schemas.github import GitHubPullRequestRead

    return GitHubPullRequestRead(
        number=number,
        title="Fix coverage",
        user_login="octocat",
        state="open",
        draft=False,
        head_ref="feature/coverage",
        head_sha=head_sha,
        base_ref="main",
        html_url=f"https://github.com/horinha04/meu-projeto/pull/{number}",
        created_at="2026-06-21T10:00:00Z",
        updated_at="2026-06-21T11:00:00Z",
    )


def _patch_open_pull_requests(monkeypatch, pull_requests):
    monkeypatch.setattr(
        "app.services.dashboard_service.github_service.list_repository_pull_requests",
        lambda db, repository_id: pull_requests,
    )
