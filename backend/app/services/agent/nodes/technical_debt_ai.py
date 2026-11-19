from __future__ import annotations

from typing import Any

from app.services.agent.nodes import pillar_error, pillar_success
from app.services.agent.prompts import TECH_DEBT_AI_SYSTEM_PROMPT
from app.services.agent.schemas import AITechDebtReview


def technical_debt_ai(state: dict[str, Any]) -> dict[str, Any]:
    """Find design smells in Python, TypeScript, JavaScript, and Go."""

    try:
        return pillar_success(
            state,
            node="technical_debt_ai",
            schema=AITechDebtReview,
            prompt=TECH_DEBT_AI_SYSTEM_PROMPT,
            review_key="technical_debt_reviews",
        )
    except Exception as exc:
        return pillar_error("technical_debt_ai", exc)
