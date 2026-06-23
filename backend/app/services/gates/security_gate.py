import json
from json import JSONDecodeError
from typing import Any

from app.models.enums import FindingCategory, FindingSeverity
from app.services.gates.types import GateFinding, GateResult


def run_security_gate(
    *,
    analysis_run,
    repository,
    quality_config,
    coverage_config,
    repository_token: str | None = None,
) -> GateResult:
    from app.services.runner_service import RunnerError, RunnerWorkspace, repository_clone_url

    blocking_severities = _blocking_severities(quality_config.security_fail_on)
    scanners = _scanner_commands(coverage_config.language.value)
    findings: list[GateFinding] = []
    scanners_run: list[str] = []
    warnings: list[str] = []

    try:
        with RunnerWorkspace(
            analysis_run.id,
            repository_clone_url(
                repository.owner,
                repository.name,
                repository_token,
            ),
        ) as workspace:
            workspace.checkout(analysis_run.head_sha)
            for scanner, command in scanners:
                result = workspace.run(command)
                if result.timed_out:
                    raise RunnerError(f"{scanner} timed out.", result)
                parsed = parse_json_output(result.stdout, scanner)
                if parsed["status"] == "error":
                    raise RunnerError(parsed["error_message"], result)
                scanners_run.append(scanner)
                findings.extend(
                    _normalize_scanner(scanner, parsed["json"], blocking_severities)
                )
    except RunnerError as exc:
        return GateResult(
            snapshot={
                "status": "error",
                "scanners_run": scanners_run,
                "blocking_reasons": [exc.message],
                "warnings": warnings,
            },
            findings=findings,
            error_message=exc.message,
        )

    return GateResult(
        snapshot=build_security_snapshot(scanners_run, findings, warnings),
        findings=findings,
    )


def normalize_semgrep(
    payload: dict[str, Any],
    *,
    blocking_severities: set[str],
) -> list[GateFinding]:
    findings: list[GateFinding] = []
    for item in payload.get("results", []):
        extra = item.get("extra") or {}
        metadata = extra.get("metadata") or {}
        severity = _normalize_severity(
            str(metadata.get("impact") or extra.get("severity") or "low")
        )
        title = str(extra.get("message") or item.get("check_id") or "Semgrep finding")
        findings.append(
            GateFinding(
                category=FindingCategory.SECURITY,
                severity=severity,
                file_path=item.get("path"),
                line_number=(item.get("start") or {}).get("line"),
                title=title,
                description=title,
                blocking=severity.value in blocking_severities,
            )
        )
    return findings


def normalize_detect_secrets(
    payload: dict[str, Any],
    *,
    blocking_severities: set[str],
) -> list[GateFinding]:
    findings: list[GateFinding] = []
    results = payload.get("results") or {}
    for path, items in results.items():
        for item in items:
            severity = FindingSeverity.HIGH
            title = str(item.get("type") or "Potential secret detected")
            findings.append(
                GateFinding(
                    category=FindingCategory.SECURITY,
                    severity=severity,
                    file_path=path,
                    line_number=item.get("line_number"),
                    title=title,
                    description=title,
                    blocking=severity.value in blocking_severities,
                )
            )
    return findings


def normalize_bandit(
    payload: dict[str, Any],
    *,
    blocking_severities: set[str],
) -> list[GateFinding]:
    findings: list[GateFinding] = []
    for item in payload.get("results", []):
        severity = _normalize_severity(str(item.get("issue_severity") or "low"))
        title = str(item.get("issue_text") or item.get("test_name") or "Bandit finding")
        findings.append(
            GateFinding(
                category=FindingCategory.SECURITY,
                severity=severity,
                file_path=item.get("filename"),
                line_number=item.get("line_number"),
                title=title,
                description=title,
                blocking=severity.value in blocking_severities,
            )
        )
    return findings


def normalize_pip_audit(
    payload: dict[str, Any],
    *,
    blocking_severities: set[str],
) -> list[GateFinding]:
    findings: list[GateFinding] = []
    for dependency in payload.get("dependencies", []):
        for vuln in dependency.get("vulns", []):
            severity = _normalize_severity(str(vuln.get("severity") or "high"))
            title = str(vuln.get("id") or "Vulnerable dependency")
            description = str(vuln.get("description") or title)
            findings.append(
                GateFinding(
                    category=FindingCategory.SECURITY,
                    severity=severity,
                    file_path=None,
                    line_number=None,
                    title=title,
                    description=description,
                    blocking=severity.value in blocking_severities,
                )
            )
    return findings


def build_security_snapshot(
    scanners_run: list[str],
    findings: list[GateFinding],
    warnings: list[str],
) -> dict:
    counts = {severity.value: 0 for severity in FindingSeverity}
    for finding in findings:
        counts[finding.severity.value] += 1
    blocking_reasons = [finding.title for finding in findings if finding.blocking]
    return {
        "status": "fail" if blocking_reasons else "pass",
        "critical": counts["critical"],
        "high": counts["high"],
        "medium": counts["medium"],
        "low": counts["low"],
        "scanners_run": scanners_run,
        "blocking_reasons": blocking_reasons,
        "warnings": warnings,
    }


def parse_json_output(output: str, scanner: str) -> dict:
    if not output.strip():
        return {
            "status": "error",
            "error_message": f"{scanner} output was empty.",
        }
    try:
        return {"status": "ok", "json": json.loads(output)}
    except JSONDecodeError:
        return {
            "status": "error",
            "error_message": f"{scanner} output was not parseable JSON.",
        }


def _scanner_commands(language: str) -> list[tuple[str, str]]:
    commands = [
        ("semgrep", "semgrep --json --config=auto ."),
        ("detect-secrets", "detect-secrets scan --all-files"),
    ]
    if language == "python":
        commands.extend(
            [
                ("bandit", "bandit -r . -f json"),
                ("pip-audit", "pip-audit -f json"),
            ]
        )
    return commands


def _normalize_scanner(
    scanner: str,
    payload: dict[str, Any],
    blocking_severities: set[str],
) -> list[GateFinding]:
    if scanner == "semgrep":
        return normalize_semgrep(payload, blocking_severities=blocking_severities)
    if scanner == "detect-secrets":
        return normalize_detect_secrets(payload, blocking_severities=blocking_severities)
    if scanner == "bandit":
        return normalize_bandit(payload, blocking_severities=blocking_severities)
    if scanner == "pip-audit":
        return normalize_pip_audit(payload, blocking_severities=blocking_severities)
    return []


def _blocking_severities(value) -> set[str]:
    if isinstance(value, list):
        return {str(item).lower() for item in value}
    if isinstance(value, dict):
        return {str(key).lower() for key, enabled in value.items() if enabled}
    return {"critical", "high"}


def _normalize_severity(value: str) -> FindingSeverity:
    normalized = value.lower()
    if normalized in {"critical", "error"}:
        return FindingSeverity.CRITICAL if normalized == "critical" else FindingSeverity.HIGH
    if normalized in {"high", "warning", "warn"}:
        return FindingSeverity.HIGH
    if normalized in {"medium", "moderate"}:
        return FindingSeverity.MEDIUM
    return FindingSeverity.LOW
