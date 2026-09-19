from types import SimpleNamespace

from app.models.enums import AnalysisRunStatus, GateDecision
from app.services.report_service import build_final_report, build_operational_error_report


def test_operational_error_report_is_not_a_gate_fail():
    run = SimpleNamespace(
        status=AnalysisRunStatus.ERROR,
        decision=None,
        error_message="pytest timed out after 180s",
        coverage_result_json={"status": "error"},
        security_result_json={},
        technical_debt_result_json={},
    )

    report = build_operational_error_report(run)

    assert "# AI Quality Gate: OPERATIONAL ERROR" in report
    assert "not** a quality-gate fail" in report
    assert "**Gate Decision:** none" in report
    assert "command, timeout, or missing report" in report.lower()
    assert "pytest timed out after 180s" in report
    assert "FAIL" not in report.split("OPERATIONAL ERROR", 1)[0]


def test_fail_report_is_not_an_operational_error():
    run = SimpleNamespace(
        status=AnalysisRunStatus.COMPLETED,
        decision=GateDecision.FAIL,
        score=None,
        coverage_result_json={
            "status": "fail",
            "pr_coverage": 62,
            "blocking_reasons": ["PR coverage 62% is below min_total_coverage 80%."],
        },
        security_result_json={"status": "pass"},
        technical_debt_result_json={"status": "pass"},
        findings=[],
    )

    report = build_final_report(run, {})

    assert "# AI Quality Gate: FAIL" in report
    assert "quality-gate fail" in report
    assert "not an operational error" in report
    assert "**Gate Decision:** FAIL" in report
    assert "OPERATIONAL ERROR" not in report
