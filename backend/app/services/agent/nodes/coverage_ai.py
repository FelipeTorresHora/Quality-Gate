from __future__ import annotations

from typing import Any

from app.services.agent.nodes import pillar_error, pillar_success
from app.services.agent.prompts import COVERAGE_AI_SYSTEM_PROMPT
from app.services.agent.schemas import AICoverageReview


def coverage_ai(state: dict[str, Any]) -> dict[str, Any]:
    """Review uncovered diff lines from the coverage digest only."""

    try:
        return pillar_success(
            state,
            node="coverage_ai",
            schema=AICoverageReview,
            prompt=COVERAGE_AI_SYSTEM_PROMPT,
            review_key="coverage_reviews",
        )
    except Exception as exc:
        return pillar_error("coverage_ai", exc)
