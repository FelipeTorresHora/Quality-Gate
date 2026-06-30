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


def test_enqueue_then_claim_returns_run_id(repository, db_session):
    run_id = _make_run(db_session, repository["id"])

    analysis_queue.enqueue(run_id)

    assert analysis_queue.claim_next() == run_id
    assert analysis_queue.claim_next() is None


def test_enqueue_is_idempotent_per_run(repository, db_session):
    run_id = _make_run(db_session, repository["id"])

    analysis_queue.enqueue(run_id)
    analysis_queue.enqueue(run_id)

    assert analysis_queue.claim_next() == run_id
    assert analysis_queue.claim_next() is None


def test_claim_next_returns_none_when_empty(db_session):
    assert analysis_queue.claim_next() is None
