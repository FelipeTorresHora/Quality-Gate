from __future__ import annotations

import asyncio
from typing import Any

MAX_PILLAR_CHARS = 8000
MAX_REVIEW_BATCHES = 12

# state.NodeOutcome uses completed | skipped | error. Callers that say "ok"
# mean completed; that is the only success literal on the state contract.


def outcome(node: str, status: str, detail: str | None = None) -> dict[str, Any]:
    # ReviewGraphState spells success as "completed". Callers that say "ok" mean that.
    if status == "ok":
        status = "completed"
    if status not in {"completed", "skipped", "error"}:
        status = "error"
    return {"node": node, "status": status, "detail": detail}


def line_allowed(
    file_path: str | None,
    line_number: int | None,
    valid_lines_by_file: dict[str, list[int]] | None,
) -> bool:
    if not file_path or not isinstance(line_number, int) or line_number < 1:
        return False
    lines = (valid_lines_by_file or {}).get(file_path)
    if not lines:
        return False
    return line_number in lines


def cap_text(text: str | None, limit: int) -> str:
    if not text:
        return ""
    if limit < 0:
        limit = 0
    return text[:limit]


def build_chat_model():
    """ChatOpenAI for one review node. Tests replace this or ChatOpenAI."""

    from langchain_openai import ChatOpenAI

    from app.core.config import get_settings

    settings = get_settings()
    return ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        temperature=0,
    )


async def await_structured(llm: Any, schema: type, messages: list[Any]) -> Any:
    """Await structured.ainvoke_structured and return a schema instance."""

    from app.services.agent.structured import ainvoke_structured

    result = await ainvoke_structured(llm, schema, messages, max_attempts=2)
    if isinstance(result, schema):
        return result
    return schema.model_validate(result)


def call_structured(llm: Any, schema: type, messages: list[Any]) -> Any:
    """Run await_structured from a sync graph node.

    LangGraph's sync invoke cannot enter an async node. The structured helper
    is still awaited, with at most two attempts.
    """

    return asyncio.run(await_structured(llm, schema, messages))


def pillar_success(
    state: dict[str, Any],
    *,
    node: str,
    schema: type,
    prompt: str,
    review_key: str,
) -> dict[str, Any]:
    text = cap_text(state.get("evidence_text"), MAX_PILLAR_CHARS)
    review = call_structured(
        build_chat_model(),
        schema,
        [("system", prompt), ("human", text)],
    )
    return {
        review_key: [review],
        "ai_findings": list(review.findings),
        "node_outcomes": [outcome(node, "completed", None)],
    }


def pillar_error(node: str, exc: BaseException) -> dict[str, Any]:
    review_key = {
        "coverage_ai": "coverage_reviews",
        "security_ai": "security_reviews",
        "technical_debt_ai": "technical_debt_reviews",
    }.get(node, "ai_findings")
    payload: dict[str, Any] = {
        "ai_findings": [],
        "node_outcomes": [outcome(node, "error", type(exc).__name__)],
    }
    if review_key != "ai_findings":
        payload[review_key] = []
    return payload
