import ast
import re
from pathlib import Path

from app.models.enums import FindingCategory, FindingSeverity
from app.services.analysis_evidence_workspace import GateExecutionEvidenceWorkspace
from app.services.gates.coverage_gate import is_source_file
from app.services.gates.types import GateFinding, GateResult
from app.services.runner_service import RunnerError


TODO_PATTERN = re.compile(r"\b(TODO|FIXME)\b", re.IGNORECASE)
BRACE_FUNCTION_PATTERN = re.compile(
    r"\b(function\s+\w+|\w+\s*=\s*\([^)]*\)\s*=>|func\s+\w+)\b"
)


def run_technical_debt_gate(
    *,
    analysis_run,
    quality_config,
    coverage_config,
    evidence_workspace: GateExecutionEvidenceWorkspace,
) -> GateResult:
    diff_error = validate_diff_evidence(
        analysis_run.changed_files_snapshot_json,
        analysis_run.diff_snapshot,
    )
    if diff_error:
        return GateResult(snapshot=diff_error, error_message=diff_error["error_message"])

    findings = detect_new_todos(
        analysis_run.changed_files_snapshot_json,
        language=coverage_config.language.value,
        fail_on_new_todo=quality_config.fail_on_new_todo,
    )

    try:
        head = evidence_workspace.prepare_head()
        for changed_file in analysis_run.changed_files_snapshot_json:
            filename = changed_file.get("filename")
            if not filename or not is_source_file(filename, coverage_config.language.value):
                continue
            path = head.path_in_repository(filename)
            if not path.exists() or not path.is_file():
                continue
            try:
                if coverage_config.language.value == "python":
                    findings.extend(
                        analyze_python_file(
                            path,
                            display_path=filename,
                            max_function_lines=quality_config.max_function_lines,
                            max_complexity=quality_config.max_complexity,
                        )
                    )
                else:
                    findings.extend(
                        analyze_brace_language_file(
                            path,
                            display_path=filename,
                            max_function_lines=quality_config.max_function_lines,
                            language=coverage_config.language.value,
                        )
                    )
            except (OSError, SyntaxError) as exc:
                return GateResult(
                    snapshot={
                        "status": "error",
                        "blocking_reasons": [str(exc)],
                    },
                    findings=findings,
                    error_message=str(exc),
                )
    except RunnerError as exc:
        return GateResult(
            snapshot={
                "status": "error",
                "blocking_reasons": [exc.message],
            },
            findings=findings,
            error_message=exc.message,
        )

    return GateResult(snapshot=build_technical_debt_snapshot(findings), findings=findings)


def validate_diff_evidence(changed_files: list[dict], diff_snapshot: str | None) -> dict | None:
    has_patch = any(item.get("patch") for item in changed_files if isinstance(item, dict))
    if not changed_files or (not diff_snapshot and not has_patch):
        return {
            "status": "error",
            "error_message": "Pull Request diff evidence is required for Technical Debt Gate.",
            "blocking_reasons": ["Pull Request diff evidence is required for Technical Debt Gate."],
        }
    return None


def detect_new_todos(
    changed_files: list[dict],
    *,
    language: str,
    fail_on_new_todo: bool,
) -> list[GateFinding]:
    findings: list[GateFinding] = []
    for changed_file in changed_files:
        filename = changed_file.get("filename")
        patch = changed_file.get("patch")
        if not filename or not patch or not is_source_file(filename, language):
            continue
        current_line = 0
        for line in patch.splitlines():
            if line.startswith("@@"):
                match = re.search(r"\+(\d+)", line)
                current_line = int(match.group(1)) - 1 if match else current_line
                continue
            if line.startswith("+") and not line.startswith("+++"):
                current_line += 1
                content = line[1:]
                if TODO_PATTERN.search(content):
                    findings.append(
                        GateFinding(
                            category=FindingCategory.TECHNICAL_DEBT,
                            severity=FindingSeverity.MEDIUM,
                            file_path=filename,
                            line_number=current_line,
                            title="New TODO/FIXME marker",
                            description="A TODO/FIXME marker was added in this Pull Request.",
                            blocking=fail_on_new_todo,
                        )
                    )
            elif not line.startswith("-"):
                current_line += 1
    return findings


def analyze_python_file(
    path: Path,
    *,
    display_path: str,
    max_function_lines: int,
    max_complexity: int,
) -> list[GateFinding]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    findings: list[GateFinding] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        end_line = getattr(node, "end_lineno", node.lineno)
        length = end_line - node.lineno + 1
        if length > max_function_lines:
            findings.append(
                GateFinding(
                    category=FindingCategory.TECHNICAL_DEBT,
                    severity=FindingSeverity.MEDIUM,
                    file_path=display_path,
                    line_number=node.lineno,
                    title="Function exceeds line limit",
                    description=f"Function {node.name} has {length} lines, above the configured limit {max_function_lines}.",
                    blocking=True,
                )
            )
        complexity = _python_complexity(node)
        if complexity > max_complexity:
            findings.append(
                GateFinding(
                    category=FindingCategory.TECHNICAL_DEBT,
                    severity=FindingSeverity.MEDIUM,
                    file_path=display_path,
                    line_number=node.lineno,
                    title="Function complexity exceeds limit",
                    description=f"Function {node.name} has complexity {complexity}, above the configured limit {max_complexity}.",
                    blocking=True,
                )
            )
    return findings


def analyze_brace_language_file(
    path: Path,
    *,
    display_path: str,
    max_function_lines: int,
    language: str,
) -> list[GateFinding]:
    findings: list[GateFinding] = []
    lines = path.read_text(encoding="utf-8").splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        if not BRACE_FUNCTION_PATTERN.search(line):
            index += 1
            continue
        start = index + 1
        brace_depth = line.count("{") - line.count("}")
        end_index = index
        while brace_depth > 0 and end_index + 1 < len(lines):
            end_index += 1
            brace_depth += lines[end_index].count("{") - lines[end_index].count("}")
        length = end_index - index + 1
        if length > max_function_lines:
            findings.append(
                GateFinding(
                    category=FindingCategory.TECHNICAL_DEBT,
                    severity=FindingSeverity.LOW,
                    file_path=display_path,
                    line_number=start,
                    title="Function exceeds line limit",
                    description=f"{language} function has {length} lines, above the configured limit {max_function_lines}.",
                    blocking=False,
                )
            )
        index = max(end_index + 1, index + 1)
    return findings


def build_technical_debt_snapshot(findings: list[GateFinding]) -> dict:
    todo_count = len([item for item in findings if item.title == "New TODO/FIXME marker"])
    length_count = len([item for item in findings if item.title == "Function exceeds line limit"])
    complexity_count = len(
        [item for item in findings if item.title == "Function complexity exceeds limit"]
    )
    blocking_reasons = [finding.title for finding in findings if finding.blocking]
    return {
        "status": "fail" if blocking_reasons else "pass",
        "new_todo_count": todo_count,
        "function_length_count": length_count,
        "complexity_count": complexity_count,
        "blocking_reasons": blocking_reasons,
        "suggestions": _suggestions(todo_count, length_count, complexity_count),
    }


def _python_complexity(node: ast.AST) -> int:
    complexity = 1
    branches = (
        ast.If,
        ast.For,
        ast.AsyncFor,
        ast.While,
        ast.ExceptHandler,
        ast.BoolOp,
        ast.IfExp,
        ast.Match,
    )
    for child in ast.walk(node):
        if child is not node and isinstance(child, branches):
            complexity += 1
    return complexity


def _suggestions(todo_count: int, length_count: int, complexity_count: int) -> list[str]:
    suggestions: list[str] = []
    if todo_count:
        suggestions.append("Resolve new TODO/FIXME markers before merging.")
    if length_count:
        suggestions.append("Split long functions into focused smaller functions.")
    if complexity_count:
        suggestions.append("Simplify branching in complex Python functions.")
    return suggestions
