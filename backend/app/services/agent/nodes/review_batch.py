from __future__ import annotations

import json
from typing import Any

from app.services.agent.nodes import (
    build_chat_model,
    call_structured,
    line_allowed,
    outcome,
)
from app.services.agent.prompts import REVIEW_BATCH_SYSTEM_PROMPT
from app.services.agent.schemas import BatchReviewOutput, InlineComment


def review_batch(state: dict[str, Any]) -> dict[str, Any]:
    """Review one diff batch and drop lines outside that batch's valid map."""

    batch = state.get("batch") or {}
    batch_id = str(batch.get("batch_id") or "")
    try:
        if not batch_id:
            raise ValueError("batch_id is required")
        valid = {
            path: list(lines)
            for path, lines in (batch.get("valid_lines_by_file") or {}).items()
        }
        review = call_structured(
            build_chat_model(),
            BatchReviewOutput,
            [
                ("system", REVIEW_BATCH_SYSTEM_PROMPT),
                ("human", _batch_prompt(batch, valid)),
            ],
        )
        comments = [
            comment
            for comment in review.inline_comments
            if line_allowed(comment.file_path, comment.line_number, valid)
        ]
        review = review.model_copy(update={"inline_comments": comments})
        return {
            "batch_reviews": [review],
            "inline_comments": comments,
            "valid_lines_by_file": valid,
            "skipped_files": [path for path in review.skipped_files if path],
            "node_outcomes": [outcome("review_batch", "completed", batch_id)],
        }
    except Exception as exc:
        return _failed_batch(exc)


def _batch_prompt(batch: dict[str, Any], valid: dict[str, list[int]]) -> str:
    return "\n".join(
        [
            f"batch_id: {batch.get('batch_id')}",
            "files: " + ", ".join(batch.get("file_paths") or []),
            "valid_lines_by_file: " + json.dumps(valid, sort_keys=True),
            "Cite only these RIGHT-side lines.",
            "diff:",
            str(batch.get("diff_text") or ""),
        ]
    )


def _failed_batch(exc: BaseException) -> dict[str, Any]:
    return {
        "batch_reviews": [],
        "inline_comments": [],
        "valid_lines_by_file": {},
        "skipped_files": [],
        "node_outcomes": [outcome("review_batch", "error", type(exc).__name__)],
    }


def kept_comments(
    comments: list[InlineComment],
    valid_lines_by_file: dict[str, list[int]] | None,
) -> list[InlineComment]:
    seen: set[tuple[str, int, str, str]] = set()
    kept: list[InlineComment] = []
    for comment in comments:
        if not line_allowed(comment.file_path, comment.line_number, valid_lines_by_file):
            continue
        key = (comment.file_path, comment.line_number, comment.title, comment.body)
        if key in seen:
            continue
        seen.add(key)
        kept.append(comment)
    return kept
