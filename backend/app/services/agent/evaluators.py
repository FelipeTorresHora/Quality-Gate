from __future__ import annotations

import json
import re
from typing import Any

from pydantic import ValidationError

from app.services.agent.schemas import AIReviewGenerated
from app.services.evidence_redaction_service import text_contains_secrets

FAIL_PASS_PHRASES = (
    "all gates passed",
    "quality gate passed",
    "gate decision is pass",
    "the pr passes",
    "pull request passed",
    "this pr passed",
)
PASS_FAIL_PHRASES = (
    "all gates failed",
    "quality gate failed",
    "gate decision is fail",
    "the pr fails",
    "pull request failed",
    "this pr failed",
)
PATH_RE = re.compile(
    r"(?<![A-Za-z0-9_./-])((?:[\w.-]+/)*[\w.-]+\.[A-Za-z][A-Za-z0-9]*)"
)


def _review_text(output: dict[str, Any]) -> str:
    parts = [
        output.get("summary") or "",
        output.get("coverage_assessment") or "",
        output.get("security_assessment") or "",
        output.get("technical_debt_assessment") or "",
        " ".join(output.get("blocking_reasons") or []),
        " ".join(output.get("suggestions") or []),
    ]
    return "\n".join(parts)


def schema_ok(output: dict[str, Any]) -> dict[str, Any]:
    try:
        AIReviewGenerated.model_validate(output)
        return {"key": "schema_ok", "score": 1.0, "comment": "AIReviewGenerated is valid."}
    except ValidationError as exc:
        return {"key": "schema_ok", "score": 0.0, "comment": str(exc)}


def decision_lock(
    output: dict[str, Any],
    *,
    decision: str | None,
    blocking_findings: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    text = _review_text(output).lower()
    errors: list[str] = []
    if decision == "fail":
        for phrase in FAIL_PASS_PHRASES:
            if phrase in text:
                errors.append(f"fail review asserted pass via {phrase!r}")
        if blocking_findings and not (output.get("blocking_reasons") or []):
            errors.append("fail with blocking findings must include blocking_reasons")
    elif decision == "pass":
        for phrase in PASS_FAIL_PHRASES:
            if phrase in text:
                errors.append(f"pass review asserted fail via {phrase!r}")
    return {
        "key": "decision_lock",
        "score": 0.0 if errors else 1.0,
        "comment": "; ".join(errors) or "Review text respects Gate Decision.",
    }


def citation_grounding(
    output: dict[str, Any],
    *,
    evidence: dict[str, Any],
) -> dict[str, Any]:
    allowed = allowed_file_paths(evidence)
    mentioned = mentioned_file_paths(_review_text(output))
    invented = sorted(path for path in mentioned if path not in allowed)
    return {
        "key": "citation_grounding",
        "score": 0.0 if invented else 1.0,
        "comment": (
            f"Invented paths: {invented}" if invented else "All cited paths are grounded."
        ),
    }


def no_secrets(output: dict[str, Any]) -> dict[str, Any]:
    blob = json.dumps(output, ensure_ascii=False, default=str)
    leaked = text_contains_secrets(blob)
    return {
        "key": "no_secrets",
        "score": 0.0 if leaked else 1.0,
        "comment": "Output matched a secret pattern." if leaked else "No secret patterns.",
    }


def score_alignment(
    output: dict[str, Any],
    *,
    decision: str | None,
    blocking_findings: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    score = output.get("score")
    errors: list[str] = []
    if not isinstance(score, int | float):
        errors.append("score is missing")
    elif decision == "fail" and score > 70:
        errors.append(f"fail score {score} exceeds 70")
    elif decision == "pass" and not blocking_findings and score < 60:
        errors.append(f"pass score {score} is below 60")
    return {
        "key": "score_alignment",
        "score": 0.0 if errors else 1.0,
        "comment": "; ".join(errors) or "Score is aligned with Gate Decision.",
    }


def must_cite(
    output: dict[str, Any],
    *,
    required: list[str],
) -> dict[str, Any]:
    text = _review_text(output)
    missing = [item for item in required if item and item not in text]
    return {
        "key": "must_cite",
        "score": 0.0 if missing else 1.0,
        "comment": f"Missing citations: {missing}" if missing else "All required citations present.",
    }


def forbidden_substrings(
    output: dict[str, Any],
    *,
    forbidden: list[str],
) -> dict[str, Any]:
    blob = json.dumps(output, ensure_ascii=False, default=str)
    hits = [item for item in forbidden if item and item in blob]
    return {
        "key": "forbidden_substrings",
        "score": 0.0 if hits else 1.0,
        "comment": f"Forbidden hits: {hits}" if hits else "No forbidden substrings.",
    }


def evaluate_review(
    output: dict[str, Any],
    *,
    evidence: dict[str, Any],
    expected: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    expected = expected or {}
    decision = expected.get("decision") or (evidence.get("analysis_run") or {}).get("decision")
    blocking = [
        finding
        for finding in (evidence.get("findings") or [])
        if finding.get("blocking")
    ]
    results = [
        schema_ok(output),
        decision_lock(output, decision=decision, blocking_findings=blocking),
        citation_grounding(output, evidence=evidence),
        no_secrets(output),
        score_alignment(output, decision=decision, blocking_findings=blocking),
    ]
    if expected.get("must_cite"):
        results.append(must_cite(output, required=list(expected["must_cite"])))
    if expected.get("forbidden_substrings"):
        results.append(
            forbidden_substrings(output, forbidden=list(expected["forbidden_substrings"]))
        )
    return results


def allowed_file_paths(evidence: dict[str, Any]) -> set[str]:
    allowed: set[str] = set()
    for finding in evidence.get("findings") or []:
        path = finding.get("file_path")
        if path:
            allowed.add(path)
    for item in evidence.get("changed_files") or []:
        if isinstance(item, dict) and item.get("filename"):
            allowed.add(item["filename"])
        elif isinstance(item, str):
            allowed.add(item)
    for path in (
        (evidence.get("gate_results") or {}).get("coverage") or {}
    ).get("changed_source_files") or []:
        if path:
            allowed.add(path)
    return allowed


def mentioned_file_paths(text: str) -> set[str]:
    return {match.group(1) for match in PATH_RE.finditer(text or "")}


def validation_errors_for_draft(
    draft: AIReviewGenerated,
    *,
    evidence: dict[str, Any],
    decision: str | None,
) -> list[str]:
    output = draft.model_dump(mode="json")
    blocking = [
        finding
        for finding in (evidence.get("findings") or [])
        if finding.get("blocking")
    ]
    results = [
        schema_ok(output),
        decision_lock(output, decision=decision, blocking_findings=blocking),
        citation_grounding(output, evidence=evidence),
        no_secrets(output),
    ]
    return [item["comment"] for item in results if item["score"] < 1]
