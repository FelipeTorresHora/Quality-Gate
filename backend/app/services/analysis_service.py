from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.core.errors import AppError
from app.models.analysis_finding import AnalysisFinding
from app.models.analysis_run import AnalysisRun
from app.models.enums import (
    AnalysisRunStatus,
    AnalysisTriggerSource,
    FindingCategory,
    FindingSeverity,
    GateDecision,
)
from app.schemas.analysis import MockAnalysisRunCreate
from app.schemas.github import PullRequestContextRead
from app.services.repository_service import get_repository


SCENARIOS = {
    "passing": {
        "decision": GateDecision.PASS,
        "score": 96,
        "coverage": {
            "status": "pass",
            "total_coverage": 88.4,
            "changed_files_coverage": 91.2,
            "coverage_drop": 0,
            "blocking_reasons": [],
        },
        "security": {
            "status": "pass",
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 1,
            "blocking_reasons": [],
        },
        "technical_debt": {
            "status": "pass",
            "blocking_reasons": [],
            "suggestions": ["Keep functions below the configured limits."],
        },
        "findings": [],
    },
    "coverage_fail": {
        "decision": GateDecision.FAIL,
        "score": 74,
        "coverage": {
            "status": "fail",
            "base_coverage": 84.2,
            "pr_coverage": 78.4,
            "coverage_drop": 5.8,
            "changed_files_coverage": 61.5,
            "blocking_reasons": [
                "Coverage fell below the configured minimum.",
                "Changed files coverage is below 75%.",
            ],
        },
        "security": {"status": "pass", "critical": 0, "high": 0, "medium": 0},
        "technical_debt": {"status": "pass", "blocking_reasons": []},
        "findings": [
            {
                "category": FindingCategory.COVERAGE,
                "severity": FindingSeverity.HIGH,
                "file_path": "src/payments/service.py",
                "line_number": 48,
                "title": "Changed file coverage is below policy",
                "description": "The changed files coverage is 61.5%, below the configured 75%.",
                "blocking": True,
            }
        ],
    },
    "security_fail": {
        "decision": GateDecision.FAIL,
        "score": 62,
        "coverage": {"status": "pass", "total_coverage": 87.1},
        "security": {
            "status": "fail",
            "critical": 0,
            "high": 1,
            "medium": 2,
            "low": 1,
            "blocking_reasons": [
                "A new admin endpoint does not show authorization checks."
            ],
        },
        "technical_debt": {"status": "pass", "blocking_reasons": []},
        "findings": [
            {
                "category": FindingCategory.SECURITY,
                "severity": FindingSeverity.HIGH,
                "file_path": "src/api/admin.py",
                "line_number": 21,
                "title": "Admin endpoint lacks authorization guard",
                "description": "The mock scenario detected a high-severity authorization risk.",
                "blocking": True,
            }
        ],
    },
    "technical_debt_fail": {
        "decision": GateDecision.FAIL,
        "score": 68,
        "coverage": {"status": "pass", "total_coverage": 86.8},
        "security": {"status": "pass", "critical": 0, "high": 0},
        "technical_debt": {
            "status": "fail",
            "blocking_reasons": [
                "A new function exceeds the configured line limit.",
                "The PR adds a TODO in a main execution path.",
            ],
            "suggestions": ["Split validation, transformation, and persistence."],
        },
        "findings": [
            {
                "category": FindingCategory.TECHNICAL_DEBT,
                "severity": FindingSeverity.MEDIUM,
                "file_path": "src/imports/runner.py",
                "line_number": 73,
                "title": "Function exceeds line limit",
                "description": "The function process_import has 142 lines in this scenario.",
                "blocking": True,
            }
        ],
    },
    "mixed_fail": {
        "decision": GateDecision.FAIL,
        "score": 51,
        "coverage": {
            "status": "fail",
            "coverage_drop": 3.1,
            "changed_files_coverage": 58.3,
        },
        "security": {"status": "fail", "critical": 1, "high": 1},
        "technical_debt": {"status": "fail", "score": 59},
        "findings": [
            {
                "category": FindingCategory.COVERAGE,
                "severity": FindingSeverity.HIGH,
                "file_path": "src/orders/service.py",
                "line_number": 112,
                "title": "Coverage regression",
                "description": "Coverage dropped more than the configured limit.",
                "blocking": True,
            },
            {
                "category": FindingCategory.SECURITY,
                "severity": FindingSeverity.CRITICAL,
                "file_path": "src/auth/callback.py",
                "line_number": 34,
                "title": "Sensitive token handling risk",
                "description": "The scenario includes a critical token handling finding.",
                "blocking": True,
            },
            {
                "category": FindingCategory.TECHNICAL_DEBT,
                "severity": FindingSeverity.MEDIUM,
                "file_path": "src/orders/processor.py",
                "line_number": 88,
                "title": "Responsibilities are mixed",
                "description": "Validation, transformation, and persistence appear in one flow.",
                "blocking": False,
            },
        ],
    },
}

ENRICHMENT_ERROR_MESSAGE = (
    "GitHub Pull Request context could not be captured. "
    "Check token permissions and try again with a new Pull Request event."
)


def list_analysis_runs(db: Session, repository_id: UUID) -> list[AnalysisRun]:
    get_repository(db, repository_id)
    return list(
        db.scalars(
            select(AnalysisRun)
            .where(AnalysisRun.repository_id == repository_id)
            .order_by(AnalysisRun.created_at.desc())
        )
    )


def get_analysis_run(db: Session, analysis_run_id: UUID) -> AnalysisRun:
    run = db.scalar(
        select(AnalysisRun)
        .options(selectinload(AnalysisRun.findings))
        .where(AnalysisRun.id == analysis_run_id)
    )
    if run is None:
        raise AppError(404, "analysis_run_not_found", "Analysis run was not found.")
    return run


def get_analysis_run_by_pr_head(
    db: Session, repository_id: UUID, pr_number: int, head_sha: str
) -> AnalysisRun | None:
    return db.scalar(
        select(AnalysisRun).where(
            AnalysisRun.repository_id == repository_id,
            AnalysisRun.pr_number == pr_number,
            AnalysisRun.head_sha == head_sha,
        )
    )


def create_mock_analysis_run(
    db: Session, repository_id: UUID, payload: MockAnalysisRunCreate
) -> AnalysisRun:
    get_repository(db, repository_id)
    if get_analysis_run_by_pr_head(
        db, repository_id, payload.pr_number, payload.head_sha
    ):
        raise AppError(
            409,
            "analysis_run_already_exists",
            "An analysis run already exists for this Pull Request head SHA.",
        )

    scenario = SCENARIOS[payload.scenario]
    now = datetime.now(UTC)
    report = _render_report(payload.scenario, scenario)
    run = AnalysisRun(
        repository_id=repository_id,
        pr_number=payload.pr_number,
        head_sha=payload.head_sha,
        status=AnalysisRunStatus.COMPLETED,
        decision=scenario["decision"],
        trigger_source=AnalysisTriggerSource.MOCK,
        score=scenario["score"],
        coverage_result_json=scenario["coverage"],
        security_result_json=scenario["security"],
        technical_debt_result_json=scenario["technical_debt"],
        pull_request_snapshot_json={},
        changed_files_snapshot_json=[],
        diff_snapshot=None,
        diff_truncated=False,
        final_report_markdown=report,
        started_at=now,
        finished_at=now,
    )
    for finding in scenario["findings"]:
        run.findings.append(AnalysisFinding(**finding))
    db.add(run)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise AppError(
            409,
            "analysis_run_already_exists",
            "An analysis run already exists for this Pull Request head SHA.",
        ) from exc
    return get_analysis_run(db, run.id)


def create_or_reuse_webhook_analysis_run(
    db: Session, repository_id: UUID, context: PullRequestContextRead | dict
) -> AnalysisRun:
    context_model = _coerce_context(context)
    pull_request = context_model.pull_request.model_dump(mode="json")
    changed_files = [
        changed_file.model_dump(mode="json")
        for changed_file in context_model.changed_files
    ]
    existing = get_analysis_run_by_pr_head(
        db,
        repository_id,
        context_model.pull_request.number,
        context_model.pull_request.head_sha,
    )
    if existing is not None:
        return get_analysis_run(db, existing.id)

    run = AnalysisRun(
        repository_id=repository_id,
        pr_number=context_model.pull_request.number,
        head_sha=context_model.pull_request.head_sha,
        status=AnalysisRunStatus.PENDING,
        decision=None,
        trigger_source=AnalysisTriggerSource.GITHUB_WEBHOOK,
        score=None,
        coverage_result_json={},
        security_result_json={},
        technical_debt_result_json={},
        pull_request_snapshot_json=pull_request,
        changed_files_snapshot_json=changed_files,
        diff_snapshot=context_model.diff_snapshot,
        diff_truncated=context_model.diff_truncated,
        final_report_markdown=None,
        error_message=None,
        started_at=None,
        finished_at=None,
    )
    return _commit_new_run_or_reuse(db, run)


def create_or_reuse_error_webhook_analysis_run(
    db: Session,
    repository_id: UUID,
    pull_request_snapshot: dict,
    error_message: str = ENRICHMENT_ERROR_MESSAGE,
) -> AnalysisRun:
    pr_number = int(pull_request_snapshot["number"])
    head_sha = str(pull_request_snapshot["head_sha"])
    existing = get_analysis_run_by_pr_head(db, repository_id, pr_number, head_sha)
    if existing is not None:
        return get_analysis_run(db, existing.id)

    run = AnalysisRun(
        repository_id=repository_id,
        pr_number=pr_number,
        head_sha=head_sha,
        status=AnalysisRunStatus.ERROR,
        decision=None,
        trigger_source=AnalysisTriggerSource.GITHUB_WEBHOOK,
        score=None,
        coverage_result_json={},
        security_result_json={},
        technical_debt_result_json={},
        pull_request_snapshot_json=pull_request_snapshot,
        changed_files_snapshot_json=[],
        diff_snapshot=None,
        diff_truncated=False,
        final_report_markdown=None,
        error_message=error_message,
        started_at=None,
        finished_at=None,
    )
    return _commit_new_run_or_reuse(db, run)


def _coerce_context(context: PullRequestContextRead | dict) -> PullRequestContextRead:
    if isinstance(context, PullRequestContextRead):
        return context
    return PullRequestContextRead.model_validate(context)


def _commit_new_run_or_reuse(db: Session, run: AnalysisRun) -> AnalysisRun:
    db.add(run)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = get_analysis_run_by_pr_head(
            db, run.repository_id, run.pr_number, run.head_sha
        )
        if existing is None:
            raise
        return get_analysis_run(db, existing.id)
    return get_analysis_run(db, run.id)


def _render_report(scenario_name: str, scenario: dict) -> str:
    decision = scenario["decision"].value.upper()
    return (
        "## AI Quality Gate\n\n"
        f"**Scenario:** `{scenario_name}`\n\n"
        f"**Decision:** {decision}\n\n"
        f"**Score:** {scenario['score']}/100\n\n"
        "This is a controlled mock analysis used to validate the dashboard."
    )
