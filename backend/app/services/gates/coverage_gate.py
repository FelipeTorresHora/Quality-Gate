from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.models.enums import FindingCategory, FindingSeverity
from app.services.coverage_parsers.cobertura import parse_cobertura_xml
from app.services.coverage_parsers.go_coverprofile import parse_go_coverprofile
from app.services.coverage_parsers.lcov import parse_lcov
from app.services.coverage_parsers.types import CoverageReport
from app.services.gates.types import GateFinding, GateResult
from app.services.runner_service import RunnerError, RunnerWorkspace, repository_clone_url


@dataclass
class ChangedCoverageResult:
    changed_files_coverage: float | None
    changed_source_files: list[str]


def run_coverage_gate(
    *,
    analysis_run,
    repository,
    quality_config,
    coverage_config,
    repository_token: str | None = None,
) -> GateResult:
    base_sha = analysis_run.pull_request_snapshot_json.get("base_sha")
    head_sha = analysis_run.head_sha
    if not base_sha or not head_sha:
        return GateResult(
            snapshot={
                "status": "error",
                "blocking_reasons": ["Pull Request base and head revisions are required."],
            },
            error_message="Pull Request base and head revisions are required.",
        )

    workspace = RunnerWorkspace(
        analysis_run.id,
        repository_clone_url(
            repository.owner,
            repository.name,
            repository_token,
        ),
    )
    try:
        with workspace:
            base_report = _run_revision_coverage(workspace, base_sha, coverage_config)
            head_report = _run_revision_coverage(workspace, head_sha, coverage_config)
    except Exception as exc:
        return GateResult(
            snapshot={
                "status": "error",
                "language": coverage_config.language.value,
                "report_format": coverage_config.report_format.value,
                "base_sha": base_sha,
                "head_sha": head_sha,
                "blocking_reasons": [str(exc)],
                "commands": workspace.command_metadata,
            },
            error_message=str(exc),
        )

    changed = calculate_changed_files_coverage(
        head_report,
        analysis_run.changed_files_snapshot_json,
        coverage_config.language.value,
    )
    snapshot, findings = apply_coverage_policy(
        language=coverage_config.language.value,
        report_format=coverage_config.report_format.value,
        base_sha=base_sha,
        head_sha=head_sha,
        base_coverage=base_report.total_coverage,
        pr_coverage=head_report.total_coverage,
        changed_files_coverage=changed.changed_files_coverage,
        changed_source_files=changed.changed_source_files,
        quality_config={
            "min_total_coverage": quality_config.min_total_coverage,
            "max_coverage_drop": quality_config.max_coverage_drop,
            "min_changed_files_coverage": quality_config.min_changed_files_coverage,
        },
        command_metadata=workspace.command_metadata,
    )
    return GateResult(snapshot=snapshot, findings=findings)


def calculate_changed_files_coverage(
    report: CoverageReport,
    changed_files: list[dict[str, Any]],
    language: str,
) -> ChangedCoverageResult:
    source_files = [
        item["filename"]
        for item in changed_files
        if isinstance(item, dict)
        and isinstance(item.get("filename"), str)
        and is_source_file(item["filename"], language)
    ]
    if not source_files:
        return ChangedCoverageResult(
            changed_files_coverage=None,
            changed_source_files=[],
        )

    percentages: list[float] = []
    normalized_report = {_normalize_path(path): value for path, value in report.files.items()}
    for filename in source_files:
        coverage = normalized_report.get(_normalize_path(filename))
        if coverage is None:
            percentages.append(0)
            continue
        percentages.append(coverage.percentage)

    percentage = round(sum(percentages) / len(percentages), 2)
    return ChangedCoverageResult(
        changed_files_coverage=percentage,
        changed_source_files=source_files,
    )


def apply_coverage_policy(
    *,
    language: str,
    report_format: str,
    base_sha: str,
    head_sha: str,
    base_coverage: float,
    pr_coverage: float,
    changed_files_coverage: float | None,
    changed_source_files: list[str],
    quality_config: dict[str, float],
    command_metadata: list[dict],
) -> tuple[dict, list[GateFinding]]:
    blocking_reasons: list[str] = []
    findings: list[GateFinding] = []
    coverage_drop = round(base_coverage - pr_coverage, 2)

    def add_failure(title: str, description: str) -> None:
        blocking_reasons.append(description)
        findings.append(
            GateFinding(
                category=FindingCategory.COVERAGE,
                severity=FindingSeverity.HIGH,
                file_path=None,
                line_number=None,
                title=title,
                description=description,
                blocking=True,
            )
        )

    if pr_coverage < quality_config["min_total_coverage"]:
        add_failure(
            "Total coverage is below policy",
            f"Pull Request coverage {pr_coverage}% is below the configured minimum {quality_config['min_total_coverage']}%.",
        )
    if coverage_drop > quality_config["max_coverage_drop"]:
        add_failure(
            "Coverage drop exceeds policy",
            f"Coverage drop {coverage_drop}% is above the configured maximum {quality_config['max_coverage_drop']}%.",
        )
    if (
        changed_files_coverage is not None
        and changed_files_coverage < quality_config["min_changed_files_coverage"]
    ):
        add_failure(
            "Changed files coverage is below policy",
            f"Changed files coverage {changed_files_coverage}% is below the configured minimum {quality_config['min_changed_files_coverage']}%.",
        )

    snapshot = {
        "status": "fail" if blocking_reasons else "pass",
        "language": language,
        "report_format": report_format,
        "base_sha": base_sha,
        "head_sha": head_sha,
        "base_coverage": base_coverage,
        "pr_coverage": pr_coverage,
        "coverage_drop": coverage_drop,
        "changed_files_coverage": changed_files_coverage,
        "changed_source_files": changed_source_files,
        "blocking_reasons": blocking_reasons,
        "commands": command_metadata,
    }
    return snapshot, findings


def is_source_file(path: str, language: str) -> bool:
    normalized = _normalize_path(path)
    parts = set(normalized.split("/"))
    if parts.intersection({"docs", "vendor", "node_modules", "dist", "build", ".venv"}):
        return False
    name = normalized.rsplit("/", 1)[-1]
    if name.startswith("."):
        return False
    if language == "python":
        return normalized.endswith(".py") and not (
            name.startswith("test_") or name.endswith("_test.py") or "/tests/" in normalized
        )
    if language == "typescript":
        return normalized.endswith((".ts", ".tsx")) and ".test." not in name and ".spec." not in name
    if language == "javascript":
        return normalized.endswith((".js", ".jsx")) and ".test." not in name and ".spec." not in name
    if language == "go":
        return normalized.endswith(".go") and not normalized.endswith("_test.go")
    return False


def _run_revision_coverage(
    workspace: RunnerWorkspace,
    revision: str,
    coverage_config,
) -> CoverageReport:
    working_directory = getattr(coverage_config, "working_directory", ".")
    workspace.checkout(revision)
    if coverage_config.install_command.strip():
        install = workspace.run(
            coverage_config.install_command,
            working_directory=working_directory,
        )
        if install.timed_out or install.exit_code != 0:
            raise RunnerError("Coverage install command failed.", install)
    test = workspace.run(
        coverage_config.test_command,
        working_directory=working_directory,
    )
    report_path = workspace.repo_path / working_directory / coverage_config.report_path
    if not report_path.exists():
        raise RunnerError("Coverage report was not produced.", test)
    return _parse_report(report_path, coverage_config.report_format.value)


def _parse_report(path: Path, report_format: str) -> CoverageReport:
    if report_format == "cobertura_xml":
        return parse_cobertura_xml(path)
    if report_format == "lcov":
        return parse_lcov(path)
    if report_format == "go_coverprofile":
        return parse_go_coverprofile(path)
    raise ValueError(f"Unsupported coverage report format: {report_format}")


def _normalize_path(path: str) -> str:
    return path.replace("\\", "/").lstrip("./")
