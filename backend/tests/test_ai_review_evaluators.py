from datetime import UTC, datetime

from app.services.agent.evaluators import (
    citation_grounding,
    decision_lock,
    evaluate_review,
    must_cite,
    no_secrets,
    schema_ok,
    score_alignment,
)
from app.services.agent.schemas import AIReviewGenerated

FAIL_COVERAGE_EVIDENCE = {
    "analysis_run": {
        "id": "00000000-0000-0000-0000-000000000002",
        "pr_number": 22,
        "head_sha": "bbb222",
        "status": "completed",
        "decision": "fail",
    },
    "changed_files": [{"filename": "app/service.py", "patch": "+def compute():\n+    return 1\n"}],
    "findings": [
        {
            "category": "coverage",
            "severity": "high",
            "file_path": "app/service.py",
            "line_number": None,
            "title": "Total coverage is below policy",
            "description": "Pull Request coverage 62% is below the configured minimum 80%.",
            "blocking": True,
        }
    ],
    "gate_results": {
        "coverage": {
            "status": "fail",
            "pr_coverage": 62.0,
            "blocking_reasons": [
                "Pull Request coverage 62% is below the configured minimum 80%."
            ],
        }
    },
}


def _generated(**overrides) -> dict:
    payload = {
        "status": "generated",
        "model": "gpt-4.1-mini",
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "score": 40,
        "summary": "Gate Decision is fail because Total coverage is below policy at 62%.",
        "risk_level": "high",
        "blocking_reasons": ["Total coverage is below policy"],
        "suggestions": ["Add tests for app/service.py until coverage reaches 80%."],
        "coverage_assessment": "pr_coverage is 62% versus min_total_coverage 80%.",
        "security_assessment": "Security completed in pass.",
        "technical_debt_assessment": "Technical debt completed in pass.",
    }
    payload.update(overrides)
    return payload


def test_fail_coverage_fixture_passes_decision_lock_and_must_cite():
    output = _generated()
    lock = decision_lock(
        output,
        decision="fail",
        blocking_findings=FAIL_COVERAGE_EVIDENCE["findings"],
    )
    cited = must_cite(output, required=["62", "Total coverage is below policy"])
    assert lock["score"] == 1.0
    assert cited["score"] == 1.0
    assert schema_ok(output)["score"] == 1.0
    AIReviewGenerated.model_validate(output)


def test_fail_coverage_contradicting_pass_fails_decision_lock():
    output = _generated(summary="All gates passed and the quality gate passed.")
    result = decision_lock(
        output,
        decision="fail",
        blocking_findings=FAIL_COVERAGE_EVIDENCE["findings"],
    )
    assert result["score"] == 0.0


def test_no_secrets_evaluator_fails_when_github_pat_appears_in_output():
    output = _generated(
        summary="Token github_pat_abcdefghijklmnopqrstuv_wxyz1234567890 leaked."
    )
    result = no_secrets(output)
    assert result["score"] == 0.0
    assert no_secrets(_generated())["score"] == 1.0


def test_citation_grounding_rejects_invented_paths():
    output = _generated(summary="See invented/module.py for the coverage drop.")
    result = citation_grounding(output, evidence=FAIL_COVERAGE_EVIDENCE)
    assert result["score"] == 0.0


def test_score_alignment_bounds():
    assert (
        score_alignment(_generated(score=40), decision="fail", blocking_findings=[{}])["score"]
        == 1.0
    )
    assert (
        score_alignment(_generated(score=91), decision="fail", blocking_findings=[{}])["score"]
        == 0.0
    )
    assert score_alignment(_generated(score=88), decision="pass", blocking_findings=[])["score"] == 1.0
    assert score_alignment(_generated(score=20), decision="pass", blocking_findings=[])["score"] == 0.0


def test_evaluate_review_aggregates_code_evaluators():
    results = evaluate_review(
        _generated(),
        evidence=FAIL_COVERAGE_EVIDENCE,
        expected={
            "decision": "fail",
            "must_cite": ["62", "Total coverage is below policy"],
            "forbidden_substrings": ["all gates passed"],
        },
    )
    assert all(item["score"] == 1.0 for item in results)
    assert {item["key"] for item in results} >= {
        "schema_ok",
        "decision_lock",
        "citation_grounding",
        "no_secrets",
        "score_alignment",
        "must_cite",
    }
