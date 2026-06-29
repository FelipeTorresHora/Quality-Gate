from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field


class AIReviewGenerated(BaseModel):
    status: Literal["generated"] = "generated"
    model: str = "gpt-4.1-mini"
    generated_at: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat().replace("+00:00", "Z")
    )
    score: int = Field(ge=0, le=100)
    summary: str
    risk_level: Literal["low", "medium", "high"]
    blocking_reasons: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    coverage_assessment: str
    security_assessment: str
    technical_debt_assessment: str


class AIReviewSkipped(BaseModel):
    status: Literal["skipped"] = "skipped"
    reason: Literal["openai_api_key_missing"] = "openai_api_key_missing"


class AIReviewError(BaseModel):
    status: Literal["error"] = "error"
    reason: Literal["ai_review_failed"] = "ai_review_failed"
    message: str = "AI review could not be generated."
