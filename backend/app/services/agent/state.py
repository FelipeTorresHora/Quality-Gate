from __future__ import annotations

import operator
from typing import Annotated, Any, Literal, TypedDict

from app.services.agent.schemas import (
    AICoverageReview,
    AIGateFinding,
    AIReviewGenerated,
    AISecurityReview,
    AITechDebtReview,
    BatchReviewOutput,
    ContextBudgetMetadata,
    InlineComment,
    PillarInsights,
)


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


class BatchInput(TypedDict):
    """One diff slice for a parallel code-review node.

    `valid_lines_by_file` is the subset of changed lines in this batch.
    Values are new-file line numbers the model may cite.
    """

    batch_id: str
    file_paths: list[str]
    diff_text: str
    valid_lines_by_file: dict[str, list[int]]


class PillarDigest(TypedDict):
    """Bounded evidence for one pillar node.

    `mode` is a GateEvaluationMode value. `deterministic_status` is the
    pillar Gate Result Snapshot status (pass, fail, skipped, or error).
    """

    pillar: Literal["coverage", "security", "technical_debt"]
    mode: Literal["hybrid", "deterministic", "ai_only"]
    deterministic_status: str | None
    evidence_text: str


class NodeOutcome(TypedDict):
    """Result of one graph node. Parallel nodes append outcomes; they do not replace the list."""

    node: str
    status: Literal["completed", "skipped", "error"]
    detail: str | None


def merge_valid_lines(
    left: dict[str, list[int]] | None,
    right: dict[str, list[int]] | None,
) -> dict[str, list[int]]:
    """Union line numbers per file, preserving first-seen order.

    Parallel batch nodes can each return the lines they validated without
    replacing another batch's map.
    """

    merged: dict[str, list[int]] = {}
    for source in (left or {}, right or {}):
        for path, lines in source.items():
            bucket = merged.setdefault(path, [])
            seen = set(bucket)
            for line in lines:
                if line not in seen:
                    bucket.append(line)
                    seen.add(line)
    return merged


class ReviewGraphState(TypedDict, total=False):
    """State for the later code-review graph. This module does not build that graph.

    Reduced keys use `operator.add` or `merge_valid_lines`. A parallel node
    returns only its own delta (a list, or a partial line map). It must not
    return the accumulated value, and it must not return None.

    Only the terminal node writes `context_budget`, `pillar_insights`, and
    `final_snapshot`. Those keys are last-write. `decision` is the Gate
    Decision already stored on the Analysis Run. Nodes may read it and must
    not write `AnalysisRun.decision`.

    `skipped_files` is the reduced accumulator. `context_budget.skipped_files`
    is the deduped copy written by the terminal node. Deduplicate before
    copying because `operator.add` can repeat a path.
    """

    run_id: str
    repository_full_name: str
    pr_number: int
    head_sha: str
    decision: str | None
    model: str
    prompt_version: str
    code_review_enabled: bool
    coverage_mode: Literal["hybrid", "deterministic", "ai_only"]
    security_mode: Literal["hybrid", "deterministic", "ai_only"]
    technical_debt_mode: Literal["hybrid", "deterministic", "ai_only"]
    batch_max_chars: int
    max_batches: int
    pillar_max_chars: int
    diff_truncated: bool
    changed_files: list[dict[str, Any]]
    evidence: dict[str, Any]

    # Planner outputs. Replaced as a whole by the planner, not reduced.
    batches: list[BatchInput]
    pillar_digests: list[PillarDigest]

    # Parallel outputs.
    valid_lines_by_file: Annotated[dict[str, list[int]], merge_valid_lines]
    batch_reviews: Annotated[list[BatchReviewOutput], operator.add]
    coverage_reviews: Annotated[list[AICoverageReview], operator.add]
    security_reviews: Annotated[list[AISecurityReview], operator.add]
    technical_debt_reviews: Annotated[list[AITechDebtReview], operator.add]
    inline_comments: Annotated[list[InlineComment], operator.add]
    ai_findings: Annotated[list[AIGateFinding], operator.add]
    skipped_files: Annotated[list[str], operator.add]
    node_outcomes: Annotated[list[NodeOutcome], operator.add]

    # Terminal outputs.
    context_budget: ContextBudgetMetadata | None
    pillar_insights: PillarInsights | None
    final_snapshot: dict[str, Any]
