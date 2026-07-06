from app.models.analysis_run import AnalysisRun
from app.services.evidence_redaction_service import redact_json_like

MAX_AI_DIFF_CHARS = 60000

SYSTEM_PROMPT = """You are reviewing a Pull Request quality gate result.

The backend has already calculated the objective Gate Decision. You must not
invent, override, or contradict that decision. Explain the persisted evidence,
identify blockers from the gate results and findings, and suggest practical
fixes. Do not mention secrets, credentials, tokens, or environment variables.
"""


def build_ai_review_input(run: AnalysisRun) -> dict:
    repository = run.repository
    quality_config = repository.quality_gate_config
    coverage_config = repository.coverage_execution_config
    diff = run.diff_snapshot or ""

    payload = {
        "analysis_run": {
            "id": str(run.id),
            "pr_number": run.pr_number,
            "head_sha": run.head_sha,
            "status": run.status.value,
            "decision": run.decision.value if run.decision else None,
        },
        "repository": {
            "owner": repository.owner,
            "name": repository.name,
            "full_name": repository.full_name,
            "default_branch": repository.default_branch,
        },
        "pull_request": run.pull_request_snapshot_json,
        "changed_files": run.changed_files_snapshot_json,
        "diff_snapshot": diff[:MAX_AI_DIFF_CHARS],
        "diff_truncated": run.diff_truncated or len(diff) > MAX_AI_DIFF_CHARS,
        "gate_results": {
            "coverage": run.coverage_result_json,
            "security": run.security_result_json,
            "technical_debt": run.technical_debt_result_json,
        },
        "findings": [
            {
                "category": finding.category.value,
                "severity": finding.severity.value,
                "file_path": finding.file_path,
                "line_number": finding.line_number,
                "title": finding.title,
                "description": finding.description,
                "blocking": finding.blocking,
            }
            for finding in run.findings
        ],
        "quality_gate_config": {
            "min_total_coverage": quality_config.min_total_coverage,
            "max_coverage_drop": quality_config.max_coverage_drop,
            "min_changed_files_coverage": quality_config.min_changed_files_coverage,
            "coverage_enabled": quality_config.coverage_enabled,
            "security_fail_on": quality_config.security_fail_on,
            "security_enabled": quality_config.security_enabled,
            "max_function_lines": quality_config.max_function_lines,
            "max_complexity": quality_config.max_complexity,
            "fail_on_new_todo": quality_config.fail_on_new_todo,
            "technical_debt_enabled": quality_config.technical_debt_enabled,
            "comment_on_github": quality_config.comment_on_github,
            "publish_github_status": quality_config.publish_github_status,
        },
        "coverage_execution_config": {
            "language": coverage_config.language.value,
            "working_directory": coverage_config.working_directory,
            "report_format": coverage_config.report_format.value,
        },
    }
    return redact_json_like(payload)
