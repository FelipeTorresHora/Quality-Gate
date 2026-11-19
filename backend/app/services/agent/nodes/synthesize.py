from __future__ import annotations

import json
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.services.agent.nodes import build_chat_model, call_structured, outcome
from app.services.agent.nodes.review_batch import kept_comments
from app.services.agent.prompts import PROMPT_VERSION, SYNTHESIZE_SYSTEM_PROMPT
from app.services.agent.schemas import (
    AIGateFinding,
    AIReviewError,
    AIReviewGenerated,
    AIReviewPartial,
    ContextBudgetMetadata,
    PillarInsights,
)
from app.services.evidence_redaction_service import redact_json_like

AI_NODES = ("review_batch", "coverage_ai", "security_ai", "technical_debt_ai")
SnapshotStatus = Literal["generated", "partial", "error"]

# AIReviewPartial.reason can only be context_budget_exhausted. An isolated node
# failure still uses that partial snapshot when sibling pillars produced
# validated output, because AIReviewError cannot carry those pillars. The
# summary names the failed node. review_truncated stays false unless the
# slicer actually dropped or clipped input.


class ReviewSynthesis(BaseModel):
    score: int = Field(ge=0, le=100)
    summary: str = Field(min_length=1)
    risk_level: Literal["low", "medium", "high"] = "medium"
    blocking_reasons: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    coverage_assessment: str = ""
    security_assessment: str = ""
    technical_debt_assessment: str = ""


def merge_ready_state(state: dict[str, Any], status: str) -> dict[str, Any]:
    """Remove diff text before synthesize_review reads the state."""

    batches = []
    for batch in state.get("batches") or []:
        cleaned = dict(batch)
        cleaned["diff_text"] = ""
        batches.append(cleaned)
    digests = []
    for digest in state.get("pillar_digests") or []:
        cleaned = dict(digest)
        cleaned["evidence_text"] = ""
        digests.append(cleaned)
    evidence = {
        key: value
        for key, value in dict(state.get("evidence") or {}).items()
        if key not in {"diff_snapshot", "diff_text", "patch"}
    }
    return {
        "batches": batches,
        "pillar_digests": digests,
        "changed_files": [],
        "evidence": evidence,
        "node_outcomes": [outcome("merge_and_validate", "completed", status)],
    }


def synthesize_review(state: dict[str, Any]) -> dict[str, Any]:
    """Merge validated structured JSON. This node is not given a raw diff."""

    try:
        status = review_status(state)
        budget = context_budget_for(state)
        valid = state.get("valid_lines_by_file") or {}
        comments = kept_comments(list(state.get("inline_comments") or []), valid)
        insights = pillar_insights(state, valid)
        draft: ReviewSynthesis | None = None
        node_status = "completed"
        detail: str | None = status
        if status != "error":
            try:
                draft = call_structured(
                    build_chat_model(),
                    ReviewSynthesis,
                    [
                        ("system", SYNTHESIZE_SYSTEM_PROMPT),
                        ("human", synthesis_payload(state, comments, insights, budget)),
                    ],
                )
            except Exception:
                node_status = "error"
                detail = "structured_output_failed"
                status = "partial" if _has_validated_output(state, comments, insights) else "error"
        snapshot = build_snapshot(
            state,
            status=status,
            draft=draft,
            comments=comments,
            insights=insights,
            budget=budget,
        )
        payload = redact_json_like(snapshot.model_dump(mode="json"))
        if payload.get("status") in {"generated", "partial"}:
            payload["prompt_version"] = state.get("prompt_version") or PROMPT_VERSION
        kept_budget = budget if payload.get("status") != "error" else None
        kept_insights = insights if payload.get("status") != "error" else None
        return {
            "context_budget": kept_budget,
            "pillar_insights": kept_insights,
            "final_snapshot": payload,
            "node_outcomes": [outcome("synthesize_review", node_status, detail)],
        }
    except Exception as exc:
        return {
            "context_budget": None,
            "pillar_insights": None,
            "final_snapshot": AIReviewError().model_dump(mode="json"),
            "node_outcomes": [outcome("synthesize_review", "error", type(exc).__name__)],
        }


def review_status(state: dict[str, Any]) -> SnapshotStatus:
    outcomes = [
        item
        for item in state.get("node_outcomes") or []
        if item.get("node") in AI_NODES
    ]
    errors = [item for item in outcomes if item.get("status") == "error"]
    completed = [item for item in outcomes if item.get("status") == "completed"]
    if errors and not completed and not _has_validated_output(state, [], None):
        return "error"
    if errors or budget_exhausted(state):
        return "partial"
    return "generated"


def budget_exhausted(state: dict[str, Any]) -> bool:
    if state.get("diff_truncated"):
        return True
    if not state.get("code_review_enabled"):
        return False
    evidence = state.get("evidence") or {}
    total = int(evidence.get("batches_total") or 0)
    sent = int(evidence.get("batches_sent") or 0)
    return total > sent


def context_budget_for(state: dict[str, Any]) -> ContextBudgetMetadata:
    evidence = state.get("evidence") or {}
    enabled = bool(state.get("code_review_enabled"))
    total = int(evidence.get("batches_total") or 0) if enabled else 0
    sent = int(evidence.get("batches_sent") or 0) if enabled else 0
    cap = _limit(state.get("max_batches"), 12)
    if enabled:
        sent = min(sent, cap)
    return ContextBudgetMetadata(
        batches_sent=sent,
        batches_total=total,
        review_truncated=budget_exhausted(state),
        skipped_files=dedupe_paths(state.get("skipped_files") or []),
        batch_max_chars=_positive(state.get("batch_max_chars")),
        max_batches=cap if cap else None,
        pillar_max_chars=_positive(state.get("pillar_max_chars")),
    )


def dedupe_paths(paths: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for path in paths:
        if not path or path in seen:
            continue
        seen.add(path)
        unique.append(path)
    return unique


def pillar_insights(
    state: dict[str, Any],
    valid_lines_by_file: dict[str, list[int]],
) -> PillarInsights:
    return PillarInsights(
        coverage=_last_review(state.get("coverage_reviews"), valid_lines_by_file),
        security=_last_review(state.get("security_reviews"), valid_lines_by_file),
        technical_debt=_last_review(state.get("technical_debt_reviews"), valid_lines_by_file),
    )


def synthesis_payload(
    state: dict[str, Any],
    comments: list[Any],
    insights: PillarInsights,
    budget: ContextBudgetMetadata,
) -> str:
    payload = {
        "decision": state.get("decision"),
        "batch_reviews": [_dump(review) for review in state.get("batch_reviews") or []],
        "pillar_insights": insights.model_dump(mode="json"),
        "inline_comments": [_dump(comment) for comment in comments],
        "node_outcomes": [
            {"node": item.get("node"), "status": item.get("status")}
            for item in state.get("node_outcomes") or []
        ],
        "context_budget": budget.model_dump(mode="json"),
    }
    return json.dumps(payload, ensure_ascii=False)


def build_snapshot(
    state: dict[str, Any],
    *,
    status: SnapshotStatus,
    draft: ReviewSynthesis | None,
    comments: list[Any],
    insights: PillarInsights,
    budget: ContextBudgetMetadata,
) -> AIReviewGenerated | AIReviewPartial | AIReviewError:
    has_output = _has_validated_output(state, comments, insights)
    if status == "error" or (draft is None and not has_output):
        return AIReviewError()
    model_name = state.get("model") or "gpt-6-luna"
    failed = [
        item.get("node")
        for item in state.get("node_outcomes") or []
        if item.get("status") == "error" and item.get("node") in AI_NODES
    ]
    if failed or draft is None or not draft.summary.strip():
        summary = _fallback_summary(state, status)
    else:
        summary = draft.summary.strip()
    risk = draft.risk_level if draft else "medium"
    if risk not in {"low", "medium", "high"}:
        risk = "medium"
    score = None if draft is None else max(0, min(100, int(draft.score)))
    coverage_assessment = _assessment(
        insights.coverage,
        "coverage_assessment",
        draft.coverage_assessment if draft else "",
    )
    security_assessment = _assessment(
        insights.security,
        "security_assessment",
        draft.security_assessment if draft else "",
    )
    debt_assessment = _assessment(
        insights.technical_debt,
        "technical_debt_assessment",
        draft.technical_debt_assessment if draft else "",
    )
    blocking = [str(item) for item in (draft.blocking_reasons if draft else [])]
    suggestions = [str(item) for item in (draft.suggestions if draft else [])]
    if status == "generated" and score is not None:
        return AIReviewGenerated(
            model=model_name,
            score=score,
            summary=summary,
            risk_level=risk,
            blocking_reasons=blocking,
            suggestions=suggestions,
            coverage_assessment=coverage_assessment,
            security_assessment=security_assessment,
            technical_debt_assessment=debt_assessment,
            inline_comments=comments,
            pillar_insights=insights,
            context_budget=budget,
        )
    return AIReviewPartial(
        model=model_name,
        score=score,
        summary=summary,
        risk_level=risk,
        blocking_reasons=blocking,
        suggestions=suggestions,
        coverage_assessment=coverage_assessment,
        security_assessment=security_assessment,
        technical_debt_assessment=debt_assessment,
        inline_comments=comments,
        pillar_insights=insights,
        context_budget=budget,
    )


def _has_validated_output(
    state: dict[str, Any],
    comments: list[Any],
    insights: PillarInsights | None,
) -> bool:
    if comments or state.get("batch_reviews") or state.get("ai_findings"):
        return True
    if insights is None:
        return bool(
            state.get("coverage_reviews")
            or state.get("security_reviews")
            or state.get("technical_debt_reviews")
        )
    return any(
        review is not None
        for review in (insights.coverage, insights.security, insights.technical_debt)
    )


def _fallback_summary(state: dict[str, Any], status: str) -> str:
    failed = [
        str(item.get("node"))
        for item in state.get("node_outcomes") or []
        if item.get("status") == "error" and item.get("node") in AI_NODES
    ]
    if failed:
        names = ", ".join(dict.fromkeys(failed))
        return f"AI review is partial because {names} failed. Other pillar results were kept."
    if status == "partial":
        return "AI review is partial because the context budget was exhausted."
    return "AI review completed from the validated structured results."


def _assessment(review: Any, attr: str, fallback: str) -> str:
    if review is not None:
        text = getattr(review, attr, None)
        if isinstance(text, str) and text.strip():
            return text
    return fallback or ""


def _last_review(reviews: list[Any] | None, valid_lines_by_file: dict[str, list[int]]) -> Any:
    if not reviews:
        return None
    review = reviews[-1]
    findings = []
    for finding in getattr(review, "findings", []) or []:
        if _finding_allowed(finding, valid_lines_by_file):
            findings.append(finding)
    if findings != list(getattr(review, "findings", []) or []):
        return review.model_copy(update={"findings": findings})
    return review


def _finding_allowed(finding: AIGateFinding, valid_lines_by_file: dict[str, list[int]]) -> bool:
    if finding.line_number is None or not finding.file_path:
        return True
    lines = valid_lines_by_file.get(finding.file_path)
    if lines is None:
        return True
    return finding.line_number in lines


def _dump(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    return value


def _limit(value: Any, ceiling: int) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        number = ceiling
    if number < 0:
        number = 0
    return min(number, ceiling)


def _positive(value: Any) -> int | None:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    if number < 1:
        return None
    return number
