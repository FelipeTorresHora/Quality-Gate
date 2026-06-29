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


def _insert_run(repository_id: str, *, with_finding: bool = False) -> str:
    with SessionLocal() as db:
        run = AnalysisRun(
            repository_id=UUID(repository_id),
            pr_number=8,
            head_sha="abc789",
            status=AnalysisRunStatus.COMPLETED,
            decision=GateDecision.FAIL,
            trigger_source=AnalysisTriggerSource.MANUAL,
            score=74,
            coverage_result_json={"status": "fail"},
            security_result_json={"status": "pass"},
            technical_debt_result_json={"status": "pass"},
            ai_review_json={},
            pull_request_snapshot_json={"number": 8},
            changed_files_snapshot_json=[],
            diff_truncated=False,
            final_report_markdown="# AI Quality Gate: FAIL",
        )
        if with_finding:
            run.findings.append(
                AnalysisFinding(
                    category=FindingCategory.COVERAGE,
                    severity=FindingSeverity.HIGH,
                    file_path="src/example.py",
                    line_number=10,
                    title="Coverage regression",
                    description="Changed code is below the configured threshold.",
                    blocking=True,
                )
            )
        db.add(run)
        db.commit()
        return str(run.id)


def test_mock_analysis_endpoint_is_removed(client, repository):
    response = client.post(
        f"/api/repositories/{repository['id']}/analysis-runs/mock",
        json={"scenario": "passing", "pr_number": 1, "head_sha": "abc"},
    )

    assert response.status_code == 404


def test_analysis_list_requires_authentication(client, repository):
    client.cookies.clear()

    response = client.get(f"/api/repositories/{repository['id']}/analysis-runs")

    assert response.status_code == 401


def test_list_analysis_runs_for_repository(client, repository):
    run_id = _insert_run(repository["id"])

    response = client.get(f"/api/repositories/{repository['id']}/analysis-runs")

    assert response.status_code == 200
    runs = response.json()
    assert len(runs) == 1
    assert runs[0]["id"] == run_id
    assert runs[0]["decision"] == "fail"
    assert runs[0]["trigger_source"] == "manual"
    assert "findings" not in runs[0]


def test_get_analysis_run_detail(client, repository):
    run_id = _insert_run(repository["id"], with_finding=True)

    response = client.get(f"/api/analysis-runs/{run_id}")

    assert response.status_code == 200
    run = response.json()
    assert run["id"] == run_id
    assert run["decision"] == "fail"
    assert run["ai_review_json"] == {}
    assert run["coverage_result_json"]["status"] == "fail"
    assert run["findings"][0]["category"] == "coverage"


def test_non_admin_cannot_execute_or_publish_analysis(
    client,
    reset_database,
    create_user_repo_access,
):
    _user, repository, cookie, csrf_token = create_user_repo_access(is_admin=False)
    run_id = _insert_run(str(repository.id))

    execute_response = client.post(
        f"/api/analysis-runs/{run_id}/execute",
        cookies={"qg_session": cookie, "qg_csrf": csrf_token},
        headers={"X-CSRF-Token": csrf_token},
    )
    publish_response = client.post(
        f"/api/analysis-runs/{run_id}/publish-github",
        cookies={"qg_session": cookie, "qg_csrf": csrf_token},
        headers={"X-CSRF-Token": csrf_token},
    )

    assert execute_response.status_code == 403
    assert publish_response.status_code == 403
    assert execute_response.json()["detail"]["code"] == "repository_admin_required"
    assert publish_response.json()["detail"]["code"] == "repository_admin_required"
