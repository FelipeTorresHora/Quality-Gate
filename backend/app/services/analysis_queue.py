from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import text

from app.db.session import SessionLocal

DEFAULT_MAX_ATTEMPTS = 1


@dataclass(frozen=True)
class ClaimedAnalysisJob:
    job_id: UUID
    analysis_run_id: UUID


def enqueue(analysis_run_id: UUID) -> None:
    with SessionLocal() as db:
        db.execute(
            text(
                "INSERT INTO analysis_jobs "
                "(id, analysis_run_id, status, attempt_count) "
                "VALUES (:id, :rid, 'queued', 0) "
                "ON CONFLICT (analysis_run_id) DO UPDATE SET "
                "status='queued', "
                "attempt_count=0, "
                "started_at=NULL, "
                "finished_at=NULL, "
                "last_error=NULL, "
                "locked_at=NULL, "
                "locked_by=NULL, "
                "updated_at=now() "
                "WHERE analysis_jobs.status IN ('completed', 'failed')"
            ),
            {"id": str(uuid4()), "rid": str(analysis_run_id)},
        )
        db.commit()


def claim_next(
    worker_id: str | None = None,
    *,
    stale_after: timedelta | None = None,
) -> ClaimedAnalysisJob | None:
    if stale_after is not None:
        requeue_stale(stale_after)

    with SessionLocal() as db:
        row = db.execute(
            text(
                "UPDATE analysis_jobs SET "
                "status='running', "
                "attempt_count=attempt_count + 1, "
                "started_at=now(), "
                "locked_at=now(), "
                "locked_by=:worker_id, "
                "updated_at=now() "
                "WHERE id = (SELECT id FROM analysis_jobs WHERE status='queued' "
                "           ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 1) "
                "RETURNING id, analysis_run_id"
            ),
            {"worker_id": worker_id},
        ).first()
        db.commit()
        return (
            ClaimedAnalysisJob(
                job_id=UUID(str(row[0])),
                analysis_run_id=UUID(str(row[1])),
            )
            if row
            else None
        )


def complete(job_id: UUID) -> None:
    with SessionLocal() as db:
        db.execute(
            text(
                "UPDATE analysis_jobs SET "
                "status='completed', "
                "finished_at=now(), "
                "last_error=NULL, "
                "locked_at=NULL, "
                "locked_by=NULL, "
                "updated_at=now() "
                "WHERE id=:job_id AND status='running'"
            ),
            {"job_id": str(job_id)},
        )
        db.commit()


def requeue_stale(max_age: timedelta) -> int:
    cutoff = datetime.now(UTC) - max_age
    with SessionLocal() as db:
        result = db.execute(
            text(
                "UPDATE analysis_jobs SET "
                "status='queued', "
                "started_at=NULL, "
                "locked_at=NULL, "
                "locked_by=NULL, "
                "updated_at=now() "
                "WHERE status='running' "
                "AND COALESCE(locked_at, started_at) < :cutoff"
            ),
            {"cutoff": cutoff},
        )
        db.commit()
        return result.rowcount


def fail(
    job_id: UUID,
    error_message: str,
    *,
    retryable: bool = True,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
) -> None:
    next_status = "queued" if retryable else "failed"
    finished_at_sql = "NULL" if retryable else "now()"
    with SessionLocal() as db:
        db.execute(
            text(
                "UPDATE analysis_jobs SET "
                f"status=CASE WHEN attempt_count < :max_attempts "
                f"THEN :retry_status ELSE 'failed' END, "
                "last_error=:error_message, "
                f"finished_at=CASE WHEN attempt_count < :max_attempts "
                f"THEN {finished_at_sql} ELSE now() END, "
                "locked_at=NULL, "
                "locked_by=NULL, "
                "updated_at=now() "
                "WHERE id=:job_id AND status='running'"
            ),
            {
                "job_id": str(job_id),
                "error_message": error_message,
                "max_attempts": max_attempts,
                "retry_status": next_status,
            },
        )
        db.commit()
