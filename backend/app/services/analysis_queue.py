from uuid import UUID, uuid4

from sqlalchemy import text

from app.db.session import SessionLocal


def enqueue(analysis_run_id: UUID) -> None:
    with SessionLocal() as db:
        db.execute(
            text(
                "INSERT INTO analysis_jobs (id, analysis_run_id, status) "
                "VALUES (:id, :rid, 'queued') "
                "ON CONFLICT (analysis_run_id) DO NOTHING"
            ),
            {"id": str(uuid4()), "rid": str(analysis_run_id)},
        )
        db.commit()


def claim_next() -> UUID | None:
    with SessionLocal() as db:
        row = db.execute(
            text(
                "UPDATE analysis_jobs SET status='running', started_at=now() "
                "WHERE id = (SELECT id FROM analysis_jobs WHERE status='queued' "
                "           ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 1) "
                "RETURNING analysis_run_id"
            )
        ).first()
        db.commit()
        return UUID(str(row[0])) if row else None
