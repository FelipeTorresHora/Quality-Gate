from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from app.core.errors import AppError
from app.models.analysis_finding import AnalysisFinding
from app.models.analysis_run import AnalysisRun
from app.models.enums import AnalysisRunStatus, GateDecision
from app.models.repository import Repository
from app.services.agent import quality_agent
from app.services.gates import coverage_gate, security_gate, technical_debt_gate
from app.services.gates.types import GateFinding, GateResult
from app.services import report_service
from app.services import github_app_auth_service, github_installation_service


def execute_analysis_run(db: Session, analysis_run_id: UUID) -> AnalysisRun:
    run = _get_run_for_execution(db, analysis_run_id)
    if run.status not in (AnalysisRunStatus.PENDING, AnalysisRunStatus.ERROR):
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

    gate_results: list[GateResult] = []

    if run.repository.quality_gate_config.coverage_enabled:
        coverage = coverage_gate.run_coverage_gate(
            analysis_run=run,
            repository=run.repository,
            quality_config=run.repository.quality_gate_config,
            coverage_config=run.repository.coverage_execution_config,
            repository_token=repository_token,
        )
    else:
        coverage = _skipped_gate("coverage_gate_disabled")
    run.coverage_result_json = coverage.snapshot
    _persist_findings(db, run, coverage.findings)
    gate_results.append(coverage)
    db.commit()
    if coverage.status == "error":
        return _finish_with_error(db, run, coverage.error_message)

    if run.repository.quality_gate_config.security_enabled:
        security = security_gate.run_security_gate(
            analysis_run=run,
            repository=run.repository,
            quality_config=run.repository.quality_gate_config,
            coverage_config=run.repository.coverage_execution_config,
            repository_token=repository_token,
        )
    else:
        security = _skipped_gate("security_gate_disabled")
    run.security_result_json = security.snapshot
    _persist_findings(db, run, security.findings)
    gate_results.append(security)
    db.commit()
    if security.status == "error":
        return _finish_with_error(db, run, security.error_message)

    if run.repository.quality_gate_config.technical_debt_enabled:
        technical_debt = technical_debt_gate.run_technical_debt_gate(
            analysis_run=run,
            repository=run.repository,
            quality_config=run.repository.quality_gate_config,
            coverage_config=run.repository.coverage_execution_config,
            repository_token=repository_token,
        )
    else:
        technical_debt = _skipped_gate("technical_debt_gate_disabled")
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
    run.ai_review_json = quality_agent.generate_ai_review_snapshot(analysis_run=run)
    run.score = (
        float(run.ai_review_json["score"])
        if run.ai_review_json.get("status") == "generated"
        and isinstance(run.ai_review_json.get("score"), int | float)
        else None
    )
    run.final_report_markdown = report_service.build_final_report(
        run, run.ai_review_json
    )
    run.finished_at = datetime.now(UTC)
    db.commit()
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
    return _get_run_for_execution(db, run.id)
