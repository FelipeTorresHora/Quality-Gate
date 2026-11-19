from __future__ import annotations

from typing import Any

from app.services.agent.nodes import pillar_error, pillar_success
from app.services.agent.prompts import SECURITY_AI_SYSTEM_PROMPT
from app.services.agent.schemas import AISecurityReview


def security_ai(state: dict[str, Any]) -> dict[str, Any]:
    """Triage scanner alerts and semantic risks from the security digest only."""

    try:
        return pillar_success(
            state,
            node="security_ai",
            schema=AISecurityReview,
            prompt=SECURITY_AI_SYSTEM_PROMPT,
            review_key="security_reviews",
        )
    except Exception as exc:
        return pillar_error("security_ai", exc)
