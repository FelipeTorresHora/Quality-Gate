from types import SimpleNamespace
from uuid import uuid4

from app.models.enums import FindingCategory, FindingSeverity


def test_security_gate_normalizes_semgrep_findings():
    from app.services.gates.security_gate import normalize_semgrep

    findings = normalize_semgrep(
        {
            "results": [
                {
                    "path": "src/app.py",
                    "start": {"line": 10},
                    "extra": {
                        "message": "Use of eval",
                        "severity": "ERROR",
                        "metadata": {"impact": "HIGH"},
                    },
                    "check_id": "python.lang.security.audit.eval",
                }
            ]
        },
        blocking_severities={"high", "critical"},
    )

    assert len(findings) == 1
    finding = findings[0]
    assert finding.category == FindingCategory.SECURITY
    assert finding.severity == FindingSeverity.HIGH
    assert finding.file_path == "src/app.py"
    assert finding.line_number == 10
    assert finding.blocking is True


def test_security_snapshot_blocks_on_configured_severities():
    from app.services.gates.security_gate import build_security_snapshot
    from app.services.gates.types import GateFinding

    snapshot = build_security_snapshot(
        scanners_run=["semgrep"],
        findings=[
            GateFinding(
                category=FindingCategory.SECURITY,
                severity=FindingSeverity.MEDIUM,
                file_path="src/app.py",
                line_number=1,
                title="Medium issue",
                description="Medium issue",
                blocking=False,
            ),
            GateFinding(
                category=FindingCategory.SECURITY,
                severity=FindingSeverity.CRITICAL,
                file_path="src/app.py",
                line_number=2,
                title="Critical issue",
                description="Critical issue",
                blocking=True,
            ),
        ],
        warnings=[],
    )

    assert snapshot["status"] == "fail"
    assert snapshot["critical"] == 1
    assert snapshot["medium"] == 1
    assert snapshot["blocking_reasons"] == ["Critical issue"]


def test_scanner_missing_output_is_operational_error():
    from app.services.gates.security_gate import parse_json_output

    result = parse_json_output("", "semgrep")

    assert result["status"] == "error"
    assert "semgrep output was empty" in result["error_message"]


def test_security_gate_uses_repository_token_for_clone(monkeypatch, tmp_path):
    from app.services import analysis_evidence_workspace
    from app.services.gates import security_gate

    seen = {}

    class FakeWorkspace:
        def __init__(self, analysis_run_id, repository_url):
            seen["analysis_run_id"] = analysis_run_id
            seen["repository_url"] = repository_url
            self.root = tmp_path / str(analysis_run_id)
            self.repo_path = self.root / "repo"
            self.command_metadata = []

        def __enter__(self):
            self.root.mkdir(parents=True, exist_ok=True)
            return self

        def __exit__(self, exc_type, exc, traceback):
            return None

        def checkout(self, revision):
            seen["revision"] = revision
            self.repo_path.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(
        analysis_evidence_workspace,
        "RunnerWorkspace",
        FakeWorkspace,
    )
    monkeypatch.setattr(security_gate, "_scanner_commands", lambda language: [])

    analysis_run = SimpleNamespace(id=uuid4(), head_sha="head-sha")
    with analysis_evidence_workspace.GateExecutionEvidenceWorkspace(
        analysis_run=analysis_run,
        repository=SimpleNamespace(owner="octo-org", name="quality-api"),
        repository_token="installation-token",
    ) as evidence_workspace:
        result = security_gate.run_security_gate(
            quality_config=SimpleNamespace(
                security_fail_on=["critical", "high"]
            ),
            coverage_config=SimpleNamespace(
                language=SimpleNamespace(value="python")
            ),
            evidence_workspace=evidence_workspace,
        )

    assert result.snapshot["status"] == "pass"
    assert seen["repository_url"] == (
        "https://x-access-token:installation-token"
        "@github.com/octo-org/quality-api.git"
    )
