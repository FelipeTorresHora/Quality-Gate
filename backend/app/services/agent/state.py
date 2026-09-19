from typing import Any, TypedDict

from app.services.agent.schemas import AIReviewGenerated


class AIReviewState(TypedDict, total=False):
    analysis_run: Any
    run_id: str
    decision: str | None
    model: str
    prompt_version: str
    evidence: dict[str, Any]
    tool_results: dict[str, Any]
    draft: AIReviewGenerated | None
    validation_errors: list[str]
    final_snapshot: dict[str, Any]
