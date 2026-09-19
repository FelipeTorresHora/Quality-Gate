from __future__ import annotations

from typing import Any, Callable

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from app.services.evidence_redaction_service import redact_text

MAX_HUNK_CHARS = 4000


def get_gate_summary(evidence: dict[str, Any]) -> dict[str, Any]:
    """Return status and metrics already computed for the three gates."""
    gates = evidence.get("gate_results") or {}
    summary: dict[str, Any] = {}
    for name in ("coverage", "security", "technical_debt"):
        snapshot = gates.get(name) or {}
        summary[name] = {
            "status": snapshot.get("status"),
            "blocking_reasons": snapshot.get("blocking_reasons") or [],
            "warnings": snapshot.get("warnings") or [],
        }
        if name == "coverage":
            summary[name].update(
                {
                    "pr_coverage": snapshot.get("pr_coverage"),
                    "base_coverage": snapshot.get("base_coverage"),
                    "coverage_drop": snapshot.get("coverage_drop"),
                    "changed_files_coverage": snapshot.get("changed_files_coverage"),
                    "unmatched": snapshot.get("unmatched")
                    or _unmatched_from_warnings(snapshot.get("warnings") or []),
                }
            )
    return summary


def list_blocking_findings(evidence: dict[str, Any]) -> list[dict[str, Any]]:
    """Return blocking findings with path, line, and title."""
    findings = []
    for finding in evidence.get("findings") or []:
        if not finding.get("blocking"):
            continue
        findings.append(
            {
                "category": finding.get("category"),
                "severity": finding.get("severity"),
                "file_path": finding.get("file_path"),
                "line_number": finding.get("line_number"),
                "title": finding.get("title"),
            }
        )
    return findings


def get_changed_file_hunk(
    evidence: dict[str, Any], filename: str, max_chars: int = MAX_HUNK_CHARS
) -> dict[str, Any]:
    """Return one redacted changed-file hunk, capped in size."""
    files = evidence.get("changed_files") or []
    match = None
    for item in files:
        if isinstance(item, dict) and item.get("filename") == filename:
            match = item
            break
    if match is None:
        return {"filename": filename, "found": False, "patch": ""}
    patch = redact_text(str(match.get("patch") or ""))
    truncated = len(patch) > max_chars
    return {
        "filename": filename,
        "found": True,
        "truncated": truncated,
        "patch": patch[:max_chars],
    }


def inspect_coverage_numbers(evidence: dict[str, Any]) -> dict[str, Any]:
    """Copy coverage totals from the persisted snapshot; do not reparse reports."""
    coverage = (evidence.get("gate_results") or {}).get("coverage") or {}
    return {
        "status": coverage.get("status"),
        "pr_coverage": coverage.get("pr_coverage"),
        "base_coverage": coverage.get("base_coverage"),
        "coverage_drop": coverage.get("coverage_drop"),
        "changed_files_coverage": coverage.get("changed_files_coverage"),
        "changed_source_files": coverage.get("changed_source_files") or [],
        "unmatched": coverage.get("unmatched")
        or _unmatched_from_warnings(coverage.get("warnings") or []),
        "blocking_reasons": coverage.get("blocking_reasons") or [],
    }


def collect_tool_results(evidence: dict[str, Any]) -> dict[str, Any]:
    blocking = list_blocking_findings(evidence)
    hunks = []
    seen: set[str] = set()
    for finding in blocking:
        path = finding.get("file_path")
        if not path or path in seen:
            continue
        seen.add(path)
        hunks.append(get_changed_file_hunk(evidence, path))
    if not hunks:
        files = evidence.get("changed_files") or []
        if files and isinstance(files[0], dict) and files[0].get("filename"):
            hunks.append(get_changed_file_hunk(evidence, files[0]["filename"]))
    return {
        "get_gate_summary": get_gate_summary(evidence),
        "list_blocking_findings": blocking,
        "inspect_coverage_numbers": inspect_coverage_numbers(evidence),
        "get_changed_file_hunk": hunks,
    }


class ChangedFileHunkArgs(BaseModel):
    filename: str = Field(description="Path of a file from changed_files_snapshot_json")


def build_review_tools(evidence: dict[str, Any]) -> list[StructuredTool]:
    """Read-only LangChain tools bound to one redacted evidence payload."""

    def _summary() -> dict[str, Any]:
        return get_gate_summary(evidence)

    def _findings() -> list[dict[str, Any]]:
        return list_blocking_findings(evidence)

    def _hunk(filename: str) -> dict[str, Any]:
        return get_changed_file_hunk(evidence, filename)

    def _coverage() -> dict[str, Any]:
        return inspect_coverage_numbers(evidence)

    return [
        StructuredTool.from_function(
            func=_summary,
            name="get_gate_summary",
            description="Return status and metrics already computed for coverage, security, and technical debt.",
        ),
        StructuredTool.from_function(
            func=_findings,
            name="list_blocking_findings",
            description="List findings with blocking=true, including path, line, and title.",
        ),
        StructuredTool.from_function(
            func=_hunk,
            name="get_changed_file_hunk",
            description="Return one redacted changed-file hunk, truncated to a character cap.",
            args_schema=ChangedFileHunkArgs,
        ),
        StructuredTool.from_function(
            func=_coverage,
            name="inspect_coverage_numbers",
            description="Copy total/drop/changed-files/unmatched numbers from the coverage snapshot.",
        ),
    ]


def invoke_review_tools(evidence: dict[str, Any]) -> dict[str, Any]:
    """Invoke the four tools so LangSmith can record tool spans when tracing is on."""
    tools = {tool.name: tool for tool in build_review_tools(evidence)}
    blocking = tools["list_blocking_findings"].invoke({})
    hunks = []
    seen: set[str] = set()
    for finding in blocking:
        path = finding.get("file_path")
        if not path or path in seen:
            continue
        seen.add(path)
        hunks.append(tools["get_changed_file_hunk"].invoke({"filename": path}))
    if not hunks:
        files = evidence.get("changed_files") or []
        if files and isinstance(files[0], dict) and files[0].get("filename"):
            hunks.append(
                tools["get_changed_file_hunk"].invoke({"filename": files[0]["filename"]})
            )
    return {
        "get_gate_summary": tools["get_gate_summary"].invoke({}),
        "list_blocking_findings": blocking,
        "inspect_coverage_numbers": tools["inspect_coverage_numbers"].invoke({}),
        "get_changed_file_hunk": hunks,
    }


def _unmatched_from_warnings(warnings: list[Any]) -> list[str] | int | None:
    return warnings or None


# Keep a callable alias for tests that want the raw functions.
TOOL_FUNCTIONS: dict[str, Callable[..., Any]] = {
    "get_gate_summary": get_gate_summary,
    "list_blocking_findings": list_blocking_findings,
    "get_changed_file_hunk": get_changed_file_hunk,
    "inspect_coverage_numbers": inspect_coverage_numbers,
}
