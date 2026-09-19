import json
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.models.enums import FindingSeverity
from app.services.gates import security_gate
from app.services.runner_service import CommandResult, RunnerError


def test_normalize_detect_secrets_bandit_and_pip_audit():
    secrets = security_gate.normalize_detect_secrets(
        {"results": {"src/a.py": [{"type": "AWS", "line_number": 3}]}},
        blocking_severities={"high"},
    )
    assert secrets[0].blocking is True

    bandit = security_gate.normalize_bandit(
        {
            "results": [
                {
                    "issue_severity": "MEDIUM",
                    "issue_text": "issue",
                    "filename": "f.py",
                    "line_number": 1,
                }
            ]
        },
        blocking_severities={"medium"},
    )
    assert bandit[0].severity == FindingSeverity.MEDIUM

    pip = security_gate.normalize_pip_audit(
        {
            "dependencies": [
                {
                    "vulns": [
                        {
                            "severity": "critical",
                            "id": "CVE-1",
                            "description": "bad",
                        }
                    ]
                }
            ]
        },
        blocking_severities={"critical"},
    )
    assert pip[0].blocking is True


def test_parse_json_output_invalid_json():
    result = security_gate.parse_json_output("{not-json", "bandit")
    assert result["status"] == "error"
    assert "parseable JSON" in result["error_message"]


def test_blocking_severities_from_dict_and_list():
    assert security_gate._blocking_severities(["High"]) == {"high"}
    assert security_gate._blocking_severities({"critical": True, "low": False}) == {
        "critical"
    }
    assert security_gate._blocking_severities(None) == {"critical", "high"}


def test_normalize_severity_variants():
    assert security_gate._normalize_severity("ERROR") == FindingSeverity.HIGH
    assert security_gate._normalize_severity("critical") == FindingSeverity.CRITICAL
    assert security_gate._normalize_severity("moderate") == FindingSeverity.MEDIUM
    assert security_gate._normalize_severity("info") == FindingSeverity.LOW


def test_normalize_scanner_unknown_returns_empty():
    assert security_gate._normalize_scanner("unknown", {}, set()) == []


def test_scanner_commands_python_includes_bandit():
    commands = dict(security_gate._scanner_commands("python"))
    assert "bandit" in commands
    assert "pip-audit" in commands
    assert "semgrep" in security_gate._scanner_commands("go")[0][0]


def test_run_security_gate_scanner_timeout(monkeypatch, tmp_path):
    class FakeHead:
        def run(self, command):
            return CommandResult(
                command=command,
                exit_code=None,
                stdout="",
                stderr="",
                duration_seconds=1,
                timed_out=True,
            )

    class FakeWorkspace:
        def prepare_head(self):
            return FakeHead()

    evidence = FakeWorkspace()
    monkeypatch.setattr(
        security_gate,
        "_scanner_commands",
        lambda language: [("semgrep", "semgrep --json .")],
    )
    result = security_gate.run_security_gate(
        quality_config=SimpleNamespace(security_fail_on=["high"]),
        coverage_config=SimpleNamespace(language=SimpleNamespace(value="python")),
        evidence_workspace=evidence,
    )
    assert result.snapshot["status"] == "error"
    assert "timed out" in result.error_message


def test_run_security_gate_parses_scanner_output(monkeypatch, tmp_path):
    payload = {"results": []}

    class FakeHead:
        def run(self, command):
            return CommandResult(
                command=command,
                exit_code=0,
                stdout=json.dumps(payload),
                stderr="",
                duration_seconds=0.1,
            )

    class FakeWorkspace:
        def prepare_head(self):
            return FakeHead()

    monkeypatch.setattr(
        security_gate,
        "_scanner_commands",
        lambda language: [("semgrep", "semgrep --json .")],
    )
    result = security_gate.run_security_gate(
        quality_config=SimpleNamespace(security_fail_on=["high"]),
        coverage_config=SimpleNamespace(language=SimpleNamespace(value="go")),
        evidence_workspace=FakeWorkspace(),
    )
    assert result.snapshot["status"] == "pass"
    assert result.snapshot["scanners_run"] == ["semgrep"]


def test_run_security_gate_empty_scanner_output(monkeypatch):
    class FakeHead:
        def run(self, command):
            return CommandResult(
                command=command,
                exit_code=0,
                stdout="",
                stderr="",
                duration_seconds=0.1,
            )

    class FakeWorkspace:
        def prepare_head(self):
            return FakeHead()

    monkeypatch.setattr(
        security_gate,
        "_scanner_commands",
        lambda language: [("semgrep", "semgrep")],
    )
    result = security_gate.run_security_gate(
        quality_config=SimpleNamespace(security_fail_on=[]),
        coverage_config=SimpleNamespace(language=SimpleNamespace(value="go")),
        evidence_workspace=FakeWorkspace(),
    )
    assert result.snapshot["status"] == "error"
