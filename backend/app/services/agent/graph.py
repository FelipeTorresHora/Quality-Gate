from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from app.core.config import get_settings
from app.services.agent.evaluators import validation_errors_for_draft
from app.services.agent.nodes import cap_text, outcome
from app.services.agent.nodes.coverage_ai import coverage_ai
from app.services.agent.nodes.review_batch import review_batch
from app.services.agent.nodes.security_ai import security_ai
from app.services.agent.nodes.synthesize import merge_ready_state, synthesize_review
from app.services.agent.nodes.technical_debt_ai import technical_debt_ai
from app.services.agent.prompts import PROMPT_VERSION, SYSTEM_PROMPT, build_ai_review_input
from app.services.agent.schemas import AIReviewError, AIReviewGenerated
from app.services.agent.state import AIReviewState, ReviewGraphState, merge_valid_lines
from app.services.agent.tools import invoke_review_tools
from app.services.evidence_redaction_service import redact_json_like, redact_text

MAX_REVIEW_BATCHES = 12
MAX_PILLAR_CHARS = 8000
_MODES = {"hybrid", "deterministic", "ai_only"}
_PILLAR_NODE = {
    "coverage": "coverage_ai",
    "security": "security_ai",
    "technical_debt": "technical_debt_ai",
}


def build_review_graph_input(
    analysis_run: Any,
    *,
    model: str,
    prompt_version: str,
) -> dict[str, Any]:
    """Map an Analysis Run onto ReviewGraphState inputs.

    The full diff stays inside evidence for prepare_context. That node hands it
    to the context slicer and replaces evidence before any model node runs.
    """

    repository = getattr(analysis_run, "repository", None)
    config = getattr(repository, "quality_gate_config", None) if repository else None
    coverage_config = (
        getattr(repository, "coverage_execution_config", None) if repository else None
    )
    decision = getattr(analysis_run, "decision", None)
    findings = [_finding_dict(finding) for finding in getattr(analysis_run, "findings", None) or []]
    coverage_result = getattr(analysis_run, "coverage_result_json", None) or {}
    security_result = getattr(analysis_run, "security_result_json", None) or {}
    debt_result = getattr(analysis_run, "technical_debt_result_json", None) or {}
    language = _enum_text(getattr(coverage_config, "language", None)) or "python"
    return {
        "run_id": str(getattr(analysis_run, "id", "") or ""),
        "repository_full_name": getattr(repository, "full_name", "") or "",
        "pr_number": int(getattr(analysis_run, "pr_number", 0) or 0),
        "head_sha": getattr(analysis_run, "head_sha", "") or "",
        "decision": _enum_text(decision),
        "model": model,
        "prompt_version": prompt_version,
        "changed_files": list(getattr(analysis_run, "changed_files_snapshot_json", None) or []),
        "diff_truncated": bool(getattr(analysis_run, "diff_truncated", False)),
        "evidence": {
            "diff_snapshot": getattr(analysis_run, "diff_snapshot", None) or "",
            "coverage_report": getattr(analysis_run, "coverage_report", None),
            "language": language,
            "working_directory": getattr(coverage_config, "working_directory", None) or ".",
            "coverage_result": coverage_result if isinstance(coverage_result, dict) else {},
            "security_result": security_result if isinstance(security_result, dict) else {},
            "technical_debt_result": debt_result if isinstance(debt_result, dict) else {},
            "security_alerts": [item for item in findings if item.get("category") == "security"],
            "debt_findings": [
                item for item in findings if item.get("category") == "technical_debt"
            ],
            "code_review_enabled": bool(getattr(config, "code_review_enabled", False)),
            "coverage_mode": _mode(getattr(config, "coverage_mode", None)),
            "security_mode": _mode(getattr(config, "security_mode", None)),
            "technical_debt_mode": _mode(getattr(config, "technical_debt_mode", None)),
        },
    }


def prepare_context(state: ReviewGraphState) -> dict[str, Any]:
    """Filter the Pull Request diff into batches and pillar digests."""

    settings = get_settings()
    evidence = dict(state.get("evidence") or {})
    changed_files = list(state.get("changed_files") or [])
    diff_text = evidence.get("diff_snapshot") or ""
    if not isinstance(diff_text, str):
        diff_text = ""
    pillar_max = _bounded(settings.ai_pillar_max_chars, MAX_PILLAR_CHARS)
    max_batches = _bounded(settings.ai_max_batches, MAX_REVIEW_BATCHES)
    code_review_enabled = bool(evidence.get("code_review_enabled", False))
    coverage_mode = _mode(evidence.get("coverage_mode"))
    security_mode = _mode(evidence.get("security_mode"))
    debt_mode = _mode(evidence.get("technical_debt_mode"))
    coverage_result = evidence.get("coverage_result") if isinstance(evidence.get("coverage_result"), dict) else {}
    security_result = evidence.get("security_result") if isinstance(evidence.get("security_result"), dict) else {}
    debt_result = evidence.get("technical_debt_result") if isinstance(evidence.get("technical_debt_result"), dict) else {}
    alerts = list(evidence.get("security_alerts") or [])
    uncovered = _uncovered_lines(evidence, changed_files, coverage_result)

    from app.services.agent.context_slicer import (
        build_coverage_digest,
        build_debt_digest,
        build_security_digest,
        slice_review_batches,
        valid_lines_for_diff,
    )

    sliced = slice_review_batches(
        diff_text,
        security_alerts=alerts,
        uncovered_lines_by_file=uncovered,
        max_batch_chars=int(settings.ai_batch_max_chars),
        max_batches=max_batches,
    )
    batches = [_batch_dict(batch) for batch in sliced.batches]
    diff_lines = valid_lines_for_diff(diff_text) if diff_text else {}
    valid_lines = merge_valid_lines(
        _normalize_lines(sliced.valid_lines_by_file),
        _normalize_lines(diff_lines),
    )
    for batch in batches:
        valid_lines = merge_valid_lines(valid_lines, batch["valid_lines_by_file"])

    outcomes: list[dict[str, Any]] = []
    if not code_review_enabled:
        outcomes.append(outcome("review_batch", "skipped", "code_review_disabled"))

    digest_calls = (
        (
            "coverage",
            coverage_mode,
            build_coverage_digest(
                mode=coverage_mode,
                deterministic_status=_gate_status(coverage_result),
                uncovered_lines_by_file=uncovered,
                diff_text=diff_text,
                pr_coverage=_optional_float(coverage_result.get("pr_coverage")),
                changed_files_coverage=_optional_float(
                    coverage_result.get("changed_files_coverage")
                ),
                blocking_reasons=list(coverage_result.get("blocking_reasons") or []),
                max_chars=pillar_max,
            ),
        ),
        (
            "security",
            security_mode,
            build_security_digest(
                mode=security_mode,
                deterministic_status=_gate_status(security_result),
                diff_text=diff_text,
                alerts=alerts,
                max_chars=pillar_max,
            ),
        ),
        (
            "technical_debt",
            debt_mode,
            build_debt_digest(
                mode=debt_mode,
                deterministic_status=_gate_status(debt_result),
                findings=list(evidence.get("debt_findings") or []),
                diff_text=diff_text,
                snapshot=debt_result if isinstance(debt_result, dict) else None,
                max_chars=pillar_max,
            ),
        ),
    )
    digests: list[dict[str, Any]] = []
    skipped = list(sliced.skipped_files or [])
    pillar_truncated = False
    for pillar, mode, result in digest_calls:
        digest = _digest_dict(result.digest, pillar, mode)
        raw_text = digest.get("evidence_text") or ""
        digest["evidence_text"] = cap_text(raw_text, pillar_max)
        if len(raw_text) > pillar_max:
            pillar_truncated = True
        if result.review_truncated:
            pillar_truncated = True
        skipped.extend(result.skipped_files or [])
        digests.append(digest)
        if mode == "deterministic":
            outcomes.append(outcome(_PILLAR_NODE[pillar], "skipped", "deterministic"))

    sent_cap = min(len(batches), max_batches) if code_review_enabled else 0
    total = int(sliced.batches_total) if code_review_enabled else 0
    sent = min(int(sliced.batches_sent), sent_cap) if code_review_enabled else 0
    truncated = bool(
        state.get("diff_truncated")
        or sliced.review_truncated
        or pillar_truncated
        or (code_review_enabled and total > sent)
    )
    return {
        "batches": batches,
        "pillar_digests": digests,
        "valid_lines_by_file": valid_lines,
        "skipped_files": [path for path in skipped if path],
        "changed_files": [],
        "evidence": {
            "batches_total": total,
            "batches_sent": sent,
            "coverage_status": _gate_status(coverage_result),
            "security_status": _gate_status(security_result),
            "technical_debt_status": _gate_status(debt_result),
        },
        "code_review_enabled": code_review_enabled,
        "coverage_mode": coverage_mode,
        "security_mode": security_mode,
        "technical_debt_mode": debt_mode,
        "batch_max_chars": int(sliced.batch_max_chars or settings.ai_batch_max_chars),
        "max_batches": min(int(sliced.max_batches or max_batches), MAX_REVIEW_BATCHES),
        "pillar_max_chars": pillar_max,
        "diff_truncated": truncated,
        "node_outcomes": outcomes,
        "model": state.get("model") or settings.openai_model,
        "prompt_version": state.get("prompt_version") or PROMPT_VERSION,
    }


def fan_out_review(state: ReviewGraphState) -> list[Send] | str:
    """Send one review batch and each non-deterministic pillar digest."""

    sends: list[Send] = []
    cap = min(_bounded(state.get("max_batches"), MAX_REVIEW_BATCHES), MAX_REVIEW_BATCHES)
    if state.get("code_review_enabled"):
        for batch in (state.get("batches") or [])[:cap]:
            sends.append(Send("review_batch", {"batch": batch}))
    limit = min(_bounded(state.get("pillar_max_chars"), MAX_PILLAR_CHARS), MAX_PILLAR_CHARS)
    for digest in state.get("pillar_digests") or []:
        if digest.get("mode") == "deterministic":
            continue
        node = _PILLAR_NODE.get(str(digest.get("pillar")))
        if node is None:
            continue
        sends.append(
            Send(
                node,
                {"evidence_text": cap_text(digest.get("evidence_text"), limit)},
            )
        )
    if not sends:
        return "merge_and_validate"
    return sends


def merge_and_validate(state: ReviewGraphState) -> dict[str, Any]:
    """Drop raw diffs and record generated, partial, or error."""

    from app.services.agent.nodes.synthesize import review_status

    try:
        status = review_status(state)
        return merge_ready_state(state, status)
    except Exception as exc:
        return {
            "batches": [],
            "pillar_digests": [],
            "changed_files": [],
            "evidence": {},
            "node_outcomes": [outcome("merge_and_validate", "error", type(exc).__name__)],
        }


def build_review_graph() -> StateGraph:
    graph = StateGraph(ReviewGraphState)
    graph.add_node("prepare_context", prepare_context)
    graph.add_node("review_batch", review_batch)
    graph.add_node("coverage_ai", coverage_ai)
    graph.add_node("security_ai", security_ai)
    graph.add_node("technical_debt_ai", technical_debt_ai)
    graph.add_node("merge_and_validate", merge_and_validate)
    graph.add_node("synthesize_review", synthesize_review)
    graph.add_edge(START, "prepare_context")
    graph.add_conditional_edges(
        "prepare_context",
        fan_out_review,
        [
            "review_batch",
            "coverage_ai",
            "security_ai",
            "technical_debt_ai",
            "merge_and_validate",
        ],
    )
    for node_name in ("review_batch", "coverage_ai", "security_ai", "technical_debt_ai"):
        graph.add_edge(node_name, "merge_and_validate")
    graph.add_edge("merge_and_validate", "synthesize_review")
    graph.add_edge("synthesize_review", END)
    return graph


def _uncovered_lines(
    evidence: dict[str, Any],
    changed_files: list[Any],
    coverage_result: dict[str, Any],
) -> dict[str, list[int]]:
    report = evidence.get("coverage_report")
    if report is not None:
        from app.services.gates.coverage_gate import uncovered_lines_by_file

        lines = uncovered_lines_by_file(
            report,
            changed_files,
            evidence.get("language") or "python",
            evidence.get("working_directory") or ".",
        )
        return _normalize_lines(lines)
    stored = coverage_result.get("uncovered_lines_by_file") if isinstance(coverage_result, dict) else None
    return _normalize_lines(stored)


def _batch_dict(batch: Any) -> dict[str, Any]:
    if not isinstance(batch, dict):
        batch = {
            "batch_id": batch.batch_id,
            "file_paths": list(batch.file_paths),
            "diff_text": batch.diff_text,
            "valid_lines_by_file": dict(batch.valid_lines_by_file),
        }
    return {
        "batch_id": str(batch.get("batch_id") or ""),
        "file_paths": [str(path) for path in batch.get("file_paths") or []],
        "diff_text": str(batch.get("diff_text") or ""),
        "valid_lines_by_file": _normalize_lines(batch.get("valid_lines_by_file")),
    }


def _digest_dict(digest: Any, pillar: str, mode: str) -> dict[str, Any]:
    if not isinstance(digest, dict):
        digest = {
            "pillar": digest.pillar,
            "mode": digest.mode,
            "deterministic_status": digest.deterministic_status,
            "evidence_text": digest.evidence_text,
        }
    return {
        "pillar": digest.get("pillar") or pillar,
        "mode": _mode(digest.get("mode"), mode),
        "deterministic_status": digest.get("deterministic_status"),
        "evidence_text": digest.get("evidence_text") or "",
    }


def _normalize_lines(lines: Any) -> dict[str, list[int]]:
    normalized: dict[str, list[int]] = {}
    if not isinstance(lines, dict):
        return normalized
    for path, values in lines.items():
        if not path:
            continue
        bucket: list[int] = []
        for value in values or []:
            try:
                number = int(value)
            except (TypeError, ValueError):
                continue
            if number >= 1 and number not in bucket:
                bucket.append(number)
        if bucket:
            normalized[str(path)] = bucket
    return normalized


def _finding_dict(finding: Any) -> dict[str, Any]:
    return {
        "category": _enum_text(getattr(finding, "category", None)),
        "severity": _enum_text(getattr(finding, "severity", None)),
        "file_path": getattr(finding, "file_path", None),
        "line_number": getattr(finding, "line_number", None),
        "title": getattr(finding, "title", "") or "",
        "description": getattr(finding, "description", "") or "",
        "blocking": bool(getattr(finding, "blocking", False)),
        "scanner": getattr(finding, "scanner", None),
        "rule_id": getattr(finding, "rule_id", None),
    }


def _mode(value: Any, default: str = "hybrid") -> str:
    text = _enum_text(value)
    if text in _MODES:
        return text
    return default


def _enum_text(value: Any) -> str | None:
    if value is None:
        return None
    raw = getattr(value, "value", value)
    return str(raw)


def _gate_status(payload: Any) -> str | None:
    if isinstance(payload, dict) and payload.get("status") is not None:
        return str(payload["status"])
    return None


def _optional_float(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    return float(value)


def _bounded(value: Any, ceiling: int) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        number = ceiling
    if number < 0:
        number = 0
    return min(number, ceiling)


def load_evidence(state: AIReviewState) -> dict[str, Any]:
    settings = get_settings()
    run = state.get("analysis_run")
    evidence = state.get("evidence")
    if run is not None:
        evidence = build_ai_review_input(run)
        decision = run.decision.value if run.decision else None
        run_id = str(run.id)
    else:
        evidence = redact_json_like(evidence or {})
        decision = state.get("decision") or (evidence.get("analysis_run") or {}).get(
            "decision"
        )
        run_id = state.get("run_id") or str((evidence.get("analysis_run") or {}).get("id") or "")
    return {
        "analysis_run": None,
        "evidence": evidence,
        "run_id": run_id,
        "decision": decision,
        "model": state.get("model") or settings.openai_model,
        "prompt_version": state.get("prompt_version") or PROMPT_VERSION,
        "validation_errors": [],
        "draft": None,
    }


def retrieve(state: AIReviewState) -> dict[str, Any]:
    evidence = state.get("evidence") or {}
    return {"tool_results": invoke_review_tools(evidence)}


def draft(state: AIReviewState) -> dict[str, Any]:
    from langchain_openai import ChatOpenAI

    settings = get_settings()
    llm = ChatOpenAI(
        model=state.get("model") or settings.openai_model,
        api_key=settings.openai_api_key,
        temperature=0,
    )
    structured_llm = llm.with_structured_output(AIReviewGenerated)
    payload = {
        "decision": state.get("decision"),
        "prompt_version": state.get("prompt_version") or PROMPT_VERSION,
        "evidence": state.get("evidence"),
        "tool_results": state.get("tool_results"),
    }
    result = structured_llm.invoke(
        [
            ("system", SYSTEM_PROMPT),
            (
                "human",
                "Review this persisted quality gate evidence. "
                "Do not invent a Gate Decision; explain the existing one.\n"
                f"{json.dumps(payload, ensure_ascii=False, default=str)}",
            ),
        ]
    )
    if isinstance(result, AIReviewGenerated):
        snapshot = result
    else:
        snapshot = AIReviewGenerated.model_validate(result)
    return {"draft": snapshot}


def validate(state: AIReviewState) -> dict[str, Any]:
    draft_review = state.get("draft")
    if draft_review is None:
        return {
            "validation_errors": ["draft is missing"],
            "final_snapshot": AIReviewError().model_dump(mode="json"),
        }

    evidence = state.get("evidence") or {}
    decision = state.get("decision")
    corrected = _correct_draft(draft_review, evidence=evidence, decision=decision)
    errors = validation_errors_for_draft(
        corrected, evidence=evidence, decision=decision
    )
    if errors:
        return {
            "draft": corrected,
            "validation_errors": errors,
            "final_snapshot": AIReviewError().model_dump(mode="json"),
        }
    snapshot = corrected.model_dump(mode="json")
    snapshot["model"] = state.get("model") or get_settings().openai_model
    snapshot["prompt_version"] = state.get("prompt_version") or PROMPT_VERSION
    return {
        "draft": corrected,
        "validation_errors": [],
        "final_snapshot": snapshot,
    }


def emit(state: AIReviewState) -> dict[str, Any]:
    if state.get("final_snapshot"):
        return {}
    return {"final_snapshot": AIReviewError().model_dump(mode="json")}


def _correct_draft(
    draft_review: AIReviewGenerated,
    *,
    evidence: dict,
    decision: str | None,
) -> AIReviewGenerated:
    data = redact_json_like(draft_review.model_dump(mode="json"))
    if isinstance(data.get("score"), int | float):
        data["score"] = int(max(0, min(100, data["score"])))
    blocking = [
        finding
        for finding in (evidence.get("findings") or [])
        if finding.get("blocking")
    ]
    if decision == "fail" and blocking and not data.get("blocking_reasons"):
        data["blocking_reasons"] = [
            finding.get("title") or finding.get("description") or "Blocking finding"
            for finding in blocking
        ]
    for field in (
        "summary",
        "coverage_assessment",
        "security_assessment",
        "technical_debt_assessment",
    ):
        if isinstance(data.get(field), str):
            data[field] = redact_text(data[field])
    data["suggestions"] = [redact_text(item) for item in data.get("suggestions") or []]
    data["blocking_reasons"] = [
        redact_text(item) for item in data.get("blocking_reasons") or []
    ]
    return AIReviewGenerated.model_validate(data)


def build_graph() -> StateGraph:
    graph = StateGraph(AIReviewState)
    graph.add_node("load_evidence", load_evidence)
    graph.add_node("retrieve", retrieve)
    graph.add_node("draft", draft)
    graph.add_node("validate", validate)
    graph.add_node("emit", emit)
    graph.add_edge(START, "load_evidence")
    graph.add_edge("load_evidence", "retrieve")
    graph.add_edge("retrieve", "draft")
    graph.add_edge("draft", "validate")
    graph.add_edge("validate", "emit")
    graph.add_edge("emit", END)
    return graph


@lru_cache(maxsize=1)
def compiled_review_graph():
    return build_review_graph().compile()
