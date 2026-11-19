from datetime import UTC, datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field, TypeAdapter, model_serializer, model_validator

from app.models.enums import FindingCategory, FindingSeverity

# Settings.openai_model is the runtime default. This fallback is used only when
# a structured snapshot omits `model`; Gate Execution overwrites it from settings.
DEFAULT_REVIEW_MODEL = "gpt-6-luna"

SecurityScanner = Literal["semgrep", "detect-secrets", "bandit", "pip-audit"]
AlertDisposition = Literal["confirm", "downgrade", "dismiss"]


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


class InlineComment(BaseModel):
    """One code-review comment anchored to a changed line.

    `line_number` must be a member of ReviewGraphState.valid_lines_by_file
    for `file_path`. The graph enforces that; this model only checks shape.
    """

    file_path: str = Field(min_length=1)
    line_number: int = Field(ge=1)
    title: str = Field(min_length=1)
    body: str = Field(min_length=1)
    severity: FindingSeverity = FindingSeverity.MEDIUM
    confidence: float = Field(ge=0, le=1)
    suggestion_code: str | None = None
    category: Literal["code_review"] = "code_review"


class BatchReviewOutput(BaseModel):
    """Structured output of one diff batch. Parallel batches append, they do not replace."""

    batch_id: str = Field(min_length=1)
    summary: str
    inline_comments: list[InlineComment] = Field(default_factory=list)
    skipped_files: list[str] = Field(default_factory=list)


class AIGateFinding(BaseModel):
    """AI Analysis Finding. source is always ai and blocking is always false (ADR 0032)."""

    category: FindingCategory
    severity: FindingSeverity
    file_path: str | None = None
    line_number: int | None = Field(default=None, ge=1)
    title: str = Field(min_length=1)
    description: str
    confidence: float = Field(ge=0, le=1)
    suggestion_code: str | None = None
    source: Literal["ai"] = "ai"
    blocking: Literal[False] = False


class AICoverageReview(BaseModel):
    summary: str
    coverage_assessment: str
    findings: list[AIGateFinding] = Field(default_factory=list)

    @model_validator(mode="after")
    def findings_are_coverage(self) -> "AICoverageReview":
        _require_finding_category(self.findings, FindingCategory.COVERAGE)
        return self


class TriagedAlert(BaseModel):
    """Security scanner alert after AI triage. Triage does not change Gate Decision."""

    scanner: SecurityScanner
    rule_id: str | None = None
    file_path: str | None = None
    line_number: int | None = Field(default=None, ge=1)
    severity: FindingSeverity
    title: str = Field(min_length=1)
    description: str
    confidence: float = Field(ge=0, le=1)
    disposition: AlertDisposition
    rationale: str
    suggestion_code: str | None = None


class AISecurityReview(BaseModel):
    summary: str
    security_assessment: str
    triaged_alerts: list[TriagedAlert] = Field(default_factory=list)
    findings: list[AIGateFinding] = Field(default_factory=list)

    @model_validator(mode="after")
    def findings_are_security(self) -> "AISecurityReview":
        _require_finding_category(self.findings, FindingCategory.SECURITY)
        return self


class AITechDebtReview(BaseModel):
    summary: str
    technical_debt_assessment: str
    findings: list[AIGateFinding] = Field(default_factory=list)

    @model_validator(mode="after")
    def findings_are_technical_debt(self) -> "AITechDebtReview":
        _require_finding_category(self.findings, FindingCategory.TECHNICAL_DEBT)
        return self


class PillarInsights(BaseModel):
    """Per-pillar AI narratives. Null means that pillar was not reviewed."""

    coverage: AICoverageReview | None = None
    security: AISecurityReview | None = None
    technical_debt: AITechDebtReview | None = None


class ContextBudgetMetadata(BaseModel):
    """How much of the Pull Request diff and pillar evidence was sent to the model.

    `batches_sent` is how many batches were invoked. `batches_total` is how many
    the planner built. `review_truncated` is true when any batch, file, or pillar
    input was dropped or clipped. `skipped_files` lists paths omitted from model input.
    """

    batches_sent: int = Field(ge=0)
    batches_total: int = Field(ge=0)
    review_truncated: bool
    skipped_files: list[str] = Field(default_factory=list)
    batch_max_chars: int | None = Field(default=None, ge=1)
    max_batches: int | None = Field(default=None, ge=1)
    pillar_max_chars: int | None = Field(default=None, ge=1)


class AIReviewGenerated(BaseModel):
    status: Literal["generated"] = "generated"
    model: str = DEFAULT_REVIEW_MODEL
    generated_at: str = Field(default_factory=_utc_now_iso)
    score: int = Field(ge=0, le=100)
    summary: str
    risk_level: Literal["low", "medium", "high"]
    blocking_reasons: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    coverage_assessment: str
    security_assessment: str
    technical_debt_assessment: str
    inline_comments: list[InlineComment] = Field(default_factory=list)
    pillar_insights: PillarInsights = Field(default_factory=PillarInsights)
    context_budget: ContextBudgetMetadata | None = None

    @model_serializer(mode="wrap")
    def serialize_model(self, handler):
        # Keep the historical generated snapshot shape until a review actually
        # produced comments, pillar insights, or a context budget.
        data = handler(self)
        if not isinstance(data, dict):
            return data
        if not data.get("inline_comments"):
            data.pop("inline_comments", None)
        insights = data.get("pillar_insights")
        if insights in (
            None,
            {},
            {"coverage": None, "security": None, "technical_debt": None},
        ):
            data.pop("pillar_insights", None)
        if data.get("context_budget") is None:
            data.pop("context_budget", None)
        return data


class AIReviewPartial(BaseModel):
    """AI Review Snapshot stored when the context budget stops the review early.

    `context_budget` is required. `inline_comments` and `pillar_insights` are
    always present, including when they are empty.
    """

    status: Literal["partial"] = "partial"
    model: str = DEFAULT_REVIEW_MODEL
    generated_at: str = Field(default_factory=_utc_now_iso)
    score: int | None = Field(default=None, ge=0, le=100)
    summary: str
    risk_level: Literal["low", "medium", "high"] = "medium"
    blocking_reasons: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    coverage_assessment: str = ""
    security_assessment: str = ""
    technical_debt_assessment: str = ""
    inline_comments: list[InlineComment] = Field(default_factory=list)
    pillar_insights: PillarInsights = Field(default_factory=PillarInsights)
    context_budget: ContextBudgetMetadata
    reason: Literal["context_budget_exhausted"] = "context_budget_exhausted"


class AIReviewSkipped(BaseModel):
    status: Literal["skipped"] = "skipped"
    reason: Literal["openai_api_key_missing"] = "openai_api_key_missing"


class AIReviewError(BaseModel):
    status: Literal["error"] = "error"
    reason: Literal["ai_review_failed"] = "ai_review_failed"
    message: str = "AI review could not be generated."


AIReviewSnapshot = Annotated[
    AIReviewGenerated | AIReviewPartial | AIReviewSkipped | AIReviewError,
    Field(discriminator="status"),
]

_AI_REVIEW_SNAPSHOT_ADAPTER = TypeAdapter(AIReviewSnapshot)


def parse_ai_review_snapshot(payload: dict | None) -> AIReviewSnapshot | None:
    """Parse a stored AI Review Snapshot.

    An empty object is the column default before a review exists and is not a
    status variant. Returns None for None or {}.
    """

    if not payload:
        return None
    return _AI_REVIEW_SNAPSHOT_ADAPTER.validate_python(payload)


def _require_finding_category(
    findings: list[AIGateFinding], category: FindingCategory
) -> None:
    for finding in findings:
        if finding.category != category:
            raise ValueError(
                f"findings must use category {category.value}, got {finding.category}"
            )
