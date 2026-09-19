from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from langgraph.graph import END, START, StateGraph

from app.core.config import get_settings
from app.services.agent.evaluators import validation_errors_for_draft
from app.services.agent.prompts import PROMPT_VERSION, SYSTEM_PROMPT, build_ai_review_input
from app.services.agent.schemas import AIReviewError, AIReviewGenerated
from app.services.agent.state import AIReviewState
from app.services.agent.tools import invoke_review_tools
from app.services.evidence_redaction_service import redact_json_like, redact_text


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
    return build_graph().compile()
