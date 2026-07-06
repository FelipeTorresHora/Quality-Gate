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
from app.services.agent.prompts import build_ai_review_input
from app.services.evidence_redaction_service import REDACTION_MARKER


def test_build_ai_review_input_redacts_diff_changed_files_and_findings(repository):
    with SessionLocal() as db:
        run = AnalysisRun(
            repository_id=repository["id"],
            pr_number=42,
            head_sha="abc123",
            status=AnalysisRunStatus.COMPLETED,
            decision=GateDecision.FAIL,
            trigger_source=AnalysisTriggerSource.GITHUB_WEBHOOK,
            pull_request_snapshot_json={"number": 42, "title": "Add secret"},
            changed_files_snapshot_json=[
                {
                    "filename": "src/app.py",
                    "patch": (
                        "+-----BEGIN OPENSSH PRIVATE KEY-----\n"
                        "+private-material\n"
                        "+-----END OPENSSH PRIVATE KEY-----"
                    ),
                }
            ],
            diff_snapshot=(
                "diff --git a/src/app.py b/src/app.py\n"
                "+GITHUB_TOKEN=github_pat_abcdefghijklmnopqrstuv_wxyz1234567890\n"
            ),
            diff_truncated=False,
        )
        run.findings.append(
            AnalysisFinding(
                category=FindingCategory.SECURITY,
                severity=FindingSeverity.HIGH,
                file_path="src/app.py",
                line_number=1,
                title="Hardcoded token",
                description="saw ghs_abcdefghijklmnopqrstuvwxyz123456 in patch",
                blocking=True,
            )
        )
        db.add(run)
        db.commit()

        persisted = db.get(AnalysisRun, run.id)
        payload = build_ai_review_input(persisted)

    assert "github_pat_abcdefghijklmnopqrstuv" not in payload["diff_snapshot"]
    assert "private-material" not in payload["changed_files"][0]["patch"]
    assert (
        "ghs_abcdefghijklmnopqrstuvwxyz123456"
        not in payload["findings"][0]["description"]
    )
    assert payload["changed_files"][0]["filename"] == "src/app.py"
    assert payload["findings"][0]["line_number"] == 1
    assert REDACTION_MARKER in payload["diff_snapshot"]
    assert REDACTION_MARKER in payload["changed_files"][0]["patch"]
