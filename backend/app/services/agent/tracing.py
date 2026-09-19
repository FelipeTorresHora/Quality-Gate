from __future__ import annotations

import os
from typing import Any

from app.core.config import Settings, get_settings
from app.models.analysis_run import AnalysisRun
from app.services.agent.prompts import PROMPT_VERSION


def configure_langsmith_from_settings(settings: Settings | None = None) -> dict[str, str]:
    """Copy LangSmith Settings onto process env before the review graph runs."""
    settings = settings or get_settings()
    enabled = bool(settings.langsmith_tracing and settings.langsmith_api_key)
    updates = {
        "LANGSMITH_TRACING": "true" if enabled else "false",
        "LANGCHAIN_TRACING_V2": "true" if enabled else "false",
        "LANGSMITH_PROJECT": settings.langsmith_project,
    }
    if settings.langsmith_api_key:
        updates["LANGSMITH_API_KEY"] = settings.langsmith_api_key
    os.environ.update(updates)
    return updates


def tracing_enabled(settings: Settings | None = None) -> bool:
    settings = settings or get_settings()
    return bool(settings.langsmith_tracing and settings.langsmith_api_key)


def build_invocation_config(
    *,
    analysis_run: AnalysisRun | None = None,
    evidence: dict[str, Any] | None = None,
    model: str,
    prompt_version: str = PROMPT_VERSION,
    run_id: str | None = None,
    decision: str | None = None,
) -> dict[str, Any]:
    evidence = evidence or {}
    analysis = evidence.get("analysis_run") or {}
    repository = evidence.get("repository") or {}
    quality_config = evidence.get("quality_gate_config") or {}

    resolved_run_id = run_id or (str(analysis_run.id) if analysis_run is not None else analysis.get("id"))
    resolved_decision = decision
    if resolved_decision is None and analysis_run is not None:
        resolved_decision = analysis_run.decision.value if analysis_run.decision else None
    if resolved_decision is None:
        resolved_decision = analysis.get("decision")

    pr_number = analysis_run.pr_number if analysis_run is not None else analysis.get("pr_number")
    head_sha = analysis_run.head_sha if analysis_run is not None else analysis.get("head_sha")
    run_status = (
        analysis_run.status.value if analysis_run is not None else analysis.get("status")
    )
    repository_full_name = (
        analysis_run.repository.full_name
        if analysis_run is not None and getattr(analysis_run, "repository", None) is not None
        else repository.get("full_name")
    )

    tags = [
        "ai-review",
        f"prompt:{prompt_version}",
        f"decision:{resolved_decision or 'none'}",
        f"model:{model}",
    ]
    metadata = {
        "analysis_run_id": resolved_run_id,
        "repository_full_name": repository_full_name,
        "pr_number": pr_number,
        "head_sha": head_sha,
        "run_status": run_status,
        "gate_decision": resolved_decision,
        "coverage_enabled": quality_config.get("coverage_enabled"),
        "security_enabled": quality_config.get("security_enabled"),
        "technical_debt_enabled": quality_config.get("technical_debt_enabled"),
        "diff_truncated": evidence.get("diff_truncated"),
        "prompt_version": prompt_version,
    }
    return {
        "run_name": "ai-review-graph",
        "tags": tags,
        "metadata": metadata,
        "configurable": {"thread_id": resolved_run_id or "ai-review"},
    }
