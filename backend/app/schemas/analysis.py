from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import (
    AnalysisRunStatus,
    AnalysisTriggerSource,
    FindingCategory,
    FindingSeverity,
    FindingSource,
    GateDecision,
)
from app.services.agent.schemas import (
    AIReviewError,
    AIReviewGenerated,
    AIReviewPartial,
    AIReviewSkipped,
)

_AI_REVIEW_MODELS = (
    AIReviewGenerated,
    AIReviewPartial,
    AIReviewSkipped,
    AIReviewError,
)


def _inline_json_schema(schema: dict[str, Any]) -> dict[str, Any]:
    defs = schema.get("$defs", {})

    def resolve(node: Any) -> Any:
        if isinstance(node, dict):
            ref = node.get("$ref")
            if isinstance(ref, str) and ref.startswith("#/$defs/"):
                return resolve(defs[ref.rsplit("/", 1)[-1]])
            return {
                key: resolve(value)
                for key, value in node.items()
                if key != "$defs"
            }
        if isinstance(node, list):
            return [resolve(item) for item in node]
        return node

    return resolve(schema)


def _ai_review_response_schema() -> dict[str, Any]:
    """OpenAPI shape for ai_review_json.

    Validation stays a dict so a stored empty object is returned unchanged.
    generated and partial document inline_comments, pillar_insights, and
    context_budget (batches_sent, batches_total, review_truncated, skipped_files).
    """

    variants = [
        _inline_json_schema(model.model_json_schema()) for model in _AI_REVIEW_MODELS
    ]
    variants.append(
        {
            "type": "object",
            "description": "Empty AI Review Snapshot stored before a review exists.",
            "additionalProperties": True,
        }
    )
    return {
        "description": (
            "AI Review Snapshot. status is generated, partial, skipped, or error. "
            "generated and partial may include inline_comments, pillar_insights, "
            "and context_budget. An empty object means no review has been stored."
        ),
        "anyOf": variants,
    }


class _AIReviewJsonSchema:
    def __get_pydantic_json_schema__(self, core_schema, handler):
        return _ai_review_response_schema()


class AnalysisFindingRead(BaseModel):
    id: UUID
    analysis_run_id: UUID
    category: FindingCategory
    severity: FindingSeverity
    file_path: str | None
    line_number: int | None
    title: str
    description: str
    blocking: bool
    source: FindingSource
    confidence: float | None
    suggestion_code: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AnalysisRunSummary(BaseModel):
    id: UUID
    repository_id: UUID
    pr_number: int
    head_sha: str
    status: AnalysisRunStatus
    decision: GateDecision | None
    trigger_source: AnalysisTriggerSource
    score: float | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None
    finished_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class AnalysisRunDetail(AnalysisRunSummary):
    coverage_result_json: dict
    security_result_json: dict
    technical_debt_result_json: dict
    ai_review_json: Annotated[dict[str, Any], _AIReviewJsonSchema()]
    pull_request_snapshot_json: dict
    changed_files_snapshot_json: list[dict]
    diff_truncated: bool
    final_report_markdown: str | None
    findings: list[AnalysisFindingRead]


class GitHubPublicationCommentResult(BaseModel):
    enabled: bool
    published: bool
    html_url: str | None = None
    skipped_reason: str | None = None


class GitHubPublicationStatusResult(BaseModel):
    enabled: bool
    published: bool
    target_sha: str | None = None
    state: str | None = None
    target_url: str | None = None
    skipped_reason: str | None = None


class GitHubPublicationResult(BaseModel):
    analysis_run_id: UUID
    comment: GitHubPublicationCommentResult
    commit_status: GitHubPublicationStatusResult
