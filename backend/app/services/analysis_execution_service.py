import time
from contextlib import nullcontext
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.core.errors import AppError
from app.models.analysis_finding import AnalysisFinding
from app.models.analysis_run import AnalysisRun
from app.models.enums import (
    AnalysisRunStatus,
    FindingCategory,
    FindingSeverity,
    FindingSource,
    GateDecision,
    GateEvaluationMode,
)
from app.models.repository import Repository
from app.services.analysis_evidence_workspace import GateExecutionEvidenceWorkspace
from app.services.agent import quality_agent
from app.services.agent.schemas import AIReviewError
from app.services.gates import coverage_gate, security_gate, technical_debt_gate
from app.services.gates.types import GateFinding, GateResult
from app.services import (
    github_app_auth_service,
    github_installation_service,
    github_publication_service,
    report_service,
    runtime_cache_service,
)


STALE_RUNNING_AFTER = timedelta(minutes=30)


def execute_analysis_run(db: Session, analysis_run_id: UUID) -> AnalysisRun:
    run = _get_run_for_execution(db, analysis_run_id)
    is_stale_running = (
        run.status == AnalysisRunStatus.RUNNING
        and run.started_at is not None
        and datetime.now(UTC) - run.started_at > STALE_RUNNING_AFTER
    )
    if (
        run.status not in (AnalysisRunStatus.PENDING, AnalysisRunStatus.ERROR)
        and not is_stale_running
    ):
        raise AppError(
            409,
            "analysis_run_not_pending",
            "Only pending or errored analysis runs can be executed.",
        )

    installation_link = (
        github_installation_service.get_active_installation_for_repository(
            db,
            run.repository_id,
        )
    )
    repository_token = github_app_auth_service.generate_installation_token(
        installation_link.installation.installation_id
    )

    now = datetime.now(UTC)
    run.status = AnalysisRunStatus.RUNNING
    run.decision = None
    run.score = None
    run.error_message = None
    run.final_report_markdown = None
    run.coverage_result_json = {}
    run.security_result_json = {}
    run.technical_debt_result_json = {}
    run.ai_review_json = {}
    run.started_at = now
    run.finished_at = None
    db.execute(delete(AnalysisFinding).where(AnalysisFinding.analysis_run_id == run.id))
    db.commit()
    github_publication_service.try_publish_pending_commit_status(db, run.id)

    try:
        finished = _run_pipeline(db, run, repository_token)
    except AppError:
        raise
    except Exception as exc:
        db.rollback()
        finished = _finish_with_error(db, run, f"Unexpected analysis failure: {exc}")
    github_publication_service.try_publish_analysis_run_to_github(db, finished.id)
    return finished


def _run_pipeline(
    db: Session, run: AnalysisRun, repository_token: str | None
) -> AnalysisRun:
    deadline = time.monotonic() + get_settings().analysis_total_timeout_seconds
    gate_results: list[GateResult] = []
    config = run.repository.quality_gate_config
    coverage_config = run.repository.coverage_execution_config
    # Checkout prep is only needed when a pillar still runs in the container.
    # ai_only pillars are handled later by their LangGraph nodes.
    needs_container = any(
        _pillar_needs_container(enabled, mode)
        for enabled, mode in (
            (config.coverage_enabled, config.coverage_mode),
            (config.security_enabled, config.security_mode),
            (config.technical_debt_enabled, config.technical_debt_mode),
        )
    )
    context = (
        GateExecutionEvidenceWorkspace(
            analysis_run=run,
            repository=run.repository,
            repository_token=repository_token,
        )
        if needs_container
        else nullcontext()
    )

    with context as evidence_workspace:
        if time.monotonic() > deadline:
            return _finish_with_error(db, run, "Analysis exceeded total time budget.")

        coverage = _resolve_pillar(
            config.coverage_enabled,
            config.coverage_mode,
            "coverage_gate_disabled",
            "coverage_mode_ai_only",
            lambda: coverage_gate.run_coverage_gate(
                analysis_run=run,
                quality_config=config,
                coverage_config=coverage_config,
                evidence_workspace=evidence_workspace,
            ),
        )
        run.coverage_result_json = coverage.snapshot
        _persist_findings(db, run, coverage.findings)
        gate_results.append(coverage)
        db.commit()
        if coverage.status == "error":
            return _finish_with_error(db, run, coverage.error_message)

        if time.monotonic() > deadline:
            return _finish_with_error(db, run, "Analysis exceeded total time budget.")

        security = _resolve_pillar(
            config.security_enabled,
            config.security_mode,
            "security_gate_disabled",
            "security_mode_ai_only",
            lambda: security_gate.run_security_gate(
                quality_config=config,
                coverage_config=coverage_config,
                evidence_workspace=evidence_workspace,
            ),
        )
        run.security_result_json = security.snapshot
        _persist_findings(db, run, security.findings)
        gate_results.append(security)
        db.commit()
        if security.status == "error":
            return _finish_with_error(db, run, security.error_message)

        if time.monotonic() > deadline:
            return _finish_with_error(db, run, "Analysis exceeded total time budget.")

        technical_debt = _resolve_pillar(
            config.technical_debt_enabled,
            config.technical_debt_mode,
            "technical_debt_gate_disabled",
            "technical_debt_mode_ai_only",
            lambda: technical_debt_gate.run_technical_debt_gate(
                analysis_run=run,
                quality_config=config,
                coverage_config=coverage_config,
                evidence_workspace=evidence_workspace,
            ),
        )
        run.technical_debt_result_json = technical_debt.snapshot
        _persist_findings(db, run, technical_debt.findings)
        gate_results.append(technical_debt)
        db.commit()
        if technical_debt.status == "error":
            return _finish_with_error(db, run, technical_debt.error_message)

    run.status = AnalysisRunStatus.COMPLETED
    run.decision = (
        GateDecision.FAIL
        if any(result.status == "fail" for result in gate_results)
        else GateDecision.PASS
    )
    # Deterministic snapshots and Gate Decision are durable before any model call.
    db.commit()
    _attach_ai_review(db, run)
    run.finished_at = datetime.now(UTC)
    db.commit()
    _expire_analysis_caches(run.repository_id)
    return _get_run_for_execution(db, run.id)


def _get_run_for_execution(db: Session, analysis_run_id: UUID) -> AnalysisRun:
    db.expire_all()
    run = db.scalar(
        select(AnalysisRun)
        .options(
            selectinload(AnalysisRun.findings),
            selectinload(AnalysisRun.repository).selectinload(
                Repository.quality_gate_config
            ),
            selectinload(AnalysisRun.repository).selectinload(
                Repository.coverage_execution_config
            ),
        )
        .where(AnalysisRun.id == analysis_run_id)
    )
    if run is None:
        raise AppError(404, "analysis_run_not_found", "Analysis run was not found.")
    return run


def _persist_findings(
    db: Session, run: AnalysisRun, findings: list[GateFinding]
) -> None:
    for finding in findings:
        db.add(
            AnalysisFinding(
                analysis_run_id=run.id,
                category=finding.category,
                severity=finding.severity,
                file_path=finding.file_path,
                line_number=finding.line_number,
                title=finding.title,
                description=finding.description,
                blocking=finding.blocking,
            )
        )


def _pillar_needs_container(enabled: bool, mode: GateEvaluationMode) -> bool:
    return bool(enabled) and mode != GateEvaluationMode.AI_ONLY


def _resolve_pillar(
    enabled: bool,
    mode: GateEvaluationMode,
    disabled_reason: str,
    ai_only_reason: str,
    run_gate,
) -> GateResult:
    """Run the container gate, or leave the pillar for its LangGraph node.

    ``deterministic`` and ``hybrid`` run the container. ``ai_only`` skips it.
    The matching AI node is selected later by ``compiled_review_graph``, which
    skips a pillar whose mode is ``deterministic``.
    """

    if not enabled:
        return _skipped_gate(disabled_reason)
    if mode == GateEvaluationMode.AI_ONLY:
        return _skipped_gate(ai_only_reason)
    return run_gate()


def _attach_ai_review(db: Session, run: AnalysisRun) -> None:
    snapshot = _load_ai_snapshot(run)
    run.ai_review_json = snapshot
    run.score = _accepted_score(snapshot)
    _persist_ai_findings(db, run, snapshot)
    run.final_report_markdown = report_service.build_final_report(run, snapshot)


def _load_ai_snapshot(run: AnalysisRun) -> dict:
    try:
        snapshot = quality_agent.generate_ai_review_snapshot(analysis_run=run)
    except Exception:
        return AIReviewError().model_dump(mode="json")
    if not isinstance(snapshot, dict):
        return AIReviewError().model_dump(mode="json")
    return snapshot


def _accepted_score(snapshot: dict) -> float | None:
    if snapshot.get("status") not in {"generated", "partial"}:
        return None
    score = snapshot.get("score")
    if isinstance(score, bool) or not isinstance(score, int | float):
        return None
    if score < 0 or score > 100:
        return None
    return float(score)


def _persist_ai_findings(db: Session, run: AnalysisRun, snapshot: dict) -> None:
    """Store AI findings without changing Gate Decision.

    Inline comments become ``code_review`` findings. Pillar insight findings
    keep their coverage, security, or technical debt category. Every row is
    ``source=ai`` and ``blocking=false``.
    """

    if snapshot.get("status") not in {"generated", "partial"}:
        return
    for comment in snapshot.get("inline_comments") or []:
        payload = _ai_comment_payload(comment)
        if payload is not None:
            _add_ai_finding(db, run, payload)
    insights = snapshot.get("pillar_insights")
    if not isinstance(insights, dict):
        return
    for pillar in ("coverage", "security", "technical_debt"):
        review = insights.get(pillar)
        if not isinstance(review, dict):
            continue
        for finding in review.get("findings") or []:
            payload = _ai_finding_payload(finding, pillar)
            if payload is not None:
                _add_ai_finding(db, run, payload)


def _ai_comment_payload(comment: object) -> dict | None:
    if not isinstance(comment, dict):
        return None
    title = comment.get("title")
    body = comment.get("body")
    file_path = comment.get("file_path")
    if not isinstance(title, str) or not title.strip():
        return None
    if not isinstance(body, str) or not body.strip():
        return None
    if not isinstance(file_path, str) or not file_path.strip():
        return None
    severity = _finding_severity(comment.get("severity"))
    if severity is None:
        return None
    return {
        "category": FindingCategory.CODE_REVIEW,
        "severity": severity,
        "file_path": file_path,
        "line_number": _finding_line(comment.get("line_number")),
        "title": title.strip(),
        "description": body.strip(),
        "confidence": _finding_confidence(comment.get("confidence")),
        "suggestion_code": _finding_suggestion(comment.get("suggestion_code")),
    }


def _ai_finding_payload(finding: object, pillar: str) -> dict | None:
    if not isinstance(finding, dict):
        return None
    title = finding.get("title")
    description = finding.get("description")
    if not isinstance(title, str) or not title.strip():
        return None
    if not isinstance(description, str):
        return None
    category = _finding_category(finding.get("category"), pillar)
    severity = _finding_severity(finding.get("severity"))
    if category is None or severity is None:
        return None
    file_path = finding.get("file_path")
    if file_path is not None and not isinstance(file_path, str):
        file_path = None
    return {
        "category": category,
        "severity": severity,
        "file_path": file_path or None,
        "line_number": _finding_line(finding.get("line_number")),
        "title": title.strip(),
        "description": description,
        "confidence": _finding_confidence(finding.get("confidence")),
        "suggestion_code": _finding_suggestion(finding.get("suggestion_code")),
    }


def _add_ai_finding(db: Session, run: AnalysisRun, payload: dict) -> None:
    db.add(
        AnalysisFinding(
            analysis_run_id=run.id,
            category=payload["category"],
            severity=payload["severity"],
            file_path=payload["file_path"],
            line_number=payload["line_number"],
            title=payload["title"],
            description=payload["description"],
            blocking=False,
            source=FindingSource.AI,
            confidence=payload["confidence"],
            suggestion_code=payload["suggestion_code"],
        )
    )


def _finding_category(value: object, pillar: str) -> FindingCategory | None:
    expected = {
        "coverage": FindingCategory.COVERAGE,
        "security": FindingCategory.SECURITY,
        "technical_debt": FindingCategory.TECHNICAL_DEBT,
    }[pillar]
    if isinstance(value, FindingCategory):
        category = value
    else:
        try:
            category = FindingCategory(str(value))
        except ValueError:
            return None
    if category != expected:
        return None
    return category


def _finding_severity(value: object) -> FindingSeverity | None:
    if isinstance(value, FindingSeverity):
        return value
    try:
        return FindingSeverity(str(value))
    except ValueError:
        return None


def _finding_line(value: object) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        return None
    return value


def _finding_confidence(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    if value < 0 or value > 1:
        return None
    return float(value)


def _finding_suggestion(value: object) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    return value


def _skipped_gate(reason: str) -> GateResult:
    return GateResult(snapshot={"status": "skipped", "reason": reason})


def _finish_with_error(
    db: Session, run: AnalysisRun, error_message: str | None
) -> AnalysisRun:
    run.status = AnalysisRunStatus.ERROR
    run.decision = None
    run.score = None
    run.error_message = error_message or "Gate execution failed."
    run.final_report_markdown = report_service.build_operational_error_report(run)
    run.finished_at = datetime.now(UTC)
    db.commit()
    _expire_analysis_caches(run.repository_id)
    return _get_run_for_execution(db, run.id)


def _expire_analysis_caches(repository_id: UUID) -> None:
    runtime_cache_service.expire_tags(
        [
            f"analysis-runs:repo:{repository_id}",
            f"pull-requests:repo:{repository_id}",
            "dashboard-summary",
        ]
    )
