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
