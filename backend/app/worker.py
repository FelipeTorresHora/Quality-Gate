import logging
import time
from uuid import UUID

from app.db.session import SessionLocal
from app.services import analysis_execution_service, analysis_queue

log = logging.getLogger("analysis-worker")


def process_next_job() -> UUID | None:
    run_id = analysis_queue.claim_next()
    if run_id is None:
        return None
    db = SessionLocal()
    try:
        analysis_execution_service.execute_analysis_run(db, run_id)
    except Exception:
        log.exception("analysis run %s failed", run_id)
    finally:
        db.close()
    return run_id


def run_forever(poll_seconds: float = 2.0) -> None:
    while True:
        if process_next_job() is None:
            time.sleep(poll_seconds)


if __name__ == "__main__":
    run_forever()
