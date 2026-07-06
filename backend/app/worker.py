import logging
import time
from uuid import UUID

from app.db.session import SessionLocal
from app.services import analysis_execution_service, analysis_queue

log = logging.getLogger("analysis-worker")


def process_next_job() -> UUID | None:
    job = analysis_queue.claim_next()
    if job is None:
        return None
    db = SessionLocal()
    try:
        analysis_execution_service.execute_analysis_run(db, job.analysis_run_id)
        analysis_queue.complete(job.job_id)
    except Exception as exc:
        analysis_queue.fail(job.job_id, str(exc))
        log.exception(
            "analysis job %s for run %s failed",
            job.job_id,
            job.analysis_run_id,
        )
    finally:
        db.close()
    return job.analysis_run_id


def run_forever(poll_seconds: float = 2.0) -> None:
    while True:
        if process_next_job() is None:
            time.sleep(poll_seconds)


if __name__ == "__main__":
    run_forever()
