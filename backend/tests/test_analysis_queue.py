from datetime import UTC, datetime, timedelta

from app.models.analysis_job import AnalysisJob
from app.models.analysis_run import AnalysisRun
from app.models.enums import AnalysisRunStatus, AnalysisTriggerSource
from app.services import analysis_queue


def _make_run(db_session, repository_id, head_sha="sha-1"):
    run = AnalysisRun(
        repository_id=repository_id,
        pr_number=1,
        head_sha=head_sha,
        status=AnalysisRunStatus.PENDING,
        trigger_source=AnalysisTriggerSource.MANUAL,
    )
    db_session.add(run)
    db_session.commit()
    return run.id


def test_claim_next_returns_job_and_marks_running(repository, db_session):
    run_id = _make_run(db_session, repository["id"])

    analysis_queue.enqueue(run_id)

    claimed = analysis_queue.claim_next()

    assert claimed is not None
    assert claimed.analysis_run_id == run_id
    assert claimed.job_id is not None
    assert analysis_queue.claim_next() is None


def test_enqueue_is_idempotent_per_run(repository, db_session):
    run_id = _make_run(db_session, repository["id"])

    analysis_queue.enqueue(run_id)
    analysis_queue.enqueue(run_id)

    claimed = analysis_queue.claim_next()

    assert claimed is not None
    assert claimed.analysis_run_id == run_id
    assert analysis_queue.claim_next() is None


def test_complete_marks_job_completed_and_allows_reenqueue(
    repository, db_session
):
    run_id = _make_run(db_session, repository["id"])
    analysis_queue.enqueue(run_id)
    claimed = analysis_queue.claim_next()

    assert claimed is not None
    analysis_queue.complete(claimed.job_id)
    analysis_queue.enqueue(run_id)
    reclaimed = analysis_queue.claim_next()

    assert reclaimed is not None
    assert reclaimed.job_id == claimed.job_id
    assert reclaimed.analysis_run_id == run_id


def test_fail_marks_job_failed_and_records_error(repository, db_session):
    run_id = _make_run(db_session, repository["id"])
    analysis_queue.enqueue(run_id)
    claimed = analysis_queue.claim_next()

    assert claimed is not None
    analysis_queue.fail(claimed.job_id, "pipeline blew up")
    db_session.expire_all()
    job = db_session.get(AnalysisJob, claimed.job_id)

    assert job is not None
    assert job.status == "failed"
    assert job.finished_at is not None
    assert job.last_error == "pipeline blew up"


def test_fail_requeues_retryable_job_until_max_attempts(
    repository, db_session
):
    run_id = _make_run(db_session, repository["id"])
    analysis_queue.enqueue(run_id)
    first_claim = analysis_queue.claim_next()

    assert first_claim is not None
    analysis_queue.fail(
        first_claim.job_id, "transient failure", max_attempts=2
    )
    retry_claim = analysis_queue.claim_next()

    assert retry_claim is not None
    assert retry_claim.job_id == first_claim.job_id
    analysis_queue.fail(
        retry_claim.job_id, "transient failure again", max_attempts=2
    )
    db_session.expire_all()
    job = db_session.get(AnalysisJob, first_claim.job_id)

    assert job is not None
    assert job.status == "failed"
    assert job.last_error == "transient failure again"


def test_claim_next_reclaims_stale_running_job(repository, db_session):
    run_id = _make_run(db_session, repository["id"])
    analysis_queue.enqueue(run_id)
    claimed = analysis_queue.claim_next()
    stale_time = datetime.now(UTC) - timedelta(minutes=10)

    assert claimed is not None
    job = db_session.get(AnalysisJob, claimed.job_id)
    assert job is not None
    job.started_at = stale_time
    job.locked_at = stale_time
    db_session.commit()

    reclaimed = analysis_queue.claim_next(stale_after=timedelta(minutes=5))

    assert reclaimed is not None
    assert reclaimed.job_id == claimed.job_id
    assert reclaimed.analysis_run_id == run_id


def test_claim_next_returns_none_when_empty(db_session):
    assert analysis_queue.claim_next() is None
