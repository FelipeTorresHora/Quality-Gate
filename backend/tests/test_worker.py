from app.models.analysis_run import AnalysisRun
from app.models.enums import AnalysisRunStatus, AnalysisTriggerSource
from app import worker
from app.services import analysis_queue


def _make_run(db_session, repository_id, head_sha="sha-w"):
    run = AnalysisRun(
        repository_id=repository_id,
        pr_number=7,
        head_sha=head_sha,
        status=AnalysisRunStatus.PENDING,
        trigger_source=AnalysisTriggerSource.MANUAL,
    )
    db_session.add(run)
    db_session.commit()
    return run.id


def test_process_next_job_executes_claimed_run(repository, db_session, monkeypatch):
    run_id = _make_run(db_session, repository["id"])
    analysis_queue.enqueue(run_id)
    executed = []
    monkeypatch.setattr(
        "app.services.analysis_execution_service.execute_analysis_run",
        lambda db, analysis_run_id: executed.append(analysis_run_id),
    )

    result = worker.process_next_job()

    assert result == run_id
    assert executed == [run_id]


def test_process_next_job_returns_none_when_empty(db_session, monkeypatch):
    called = []
    monkeypatch.setattr(
        "app.services.analysis_execution_service.execute_analysis_run",
        lambda db, analysis_run_id: called.append(analysis_run_id),
    )

    assert worker.process_next_job() is None
    assert called == []


def test_process_next_job_swallows_execution_errors(
    repository, db_session, monkeypatch
):
    run_id = _make_run(db_session, repository["id"])
    analysis_queue.enqueue(run_id)

    def boom(db, analysis_run_id):
        raise RuntimeError("pipeline blew up")

    monkeypatch.setattr(
        "app.services.analysis_execution_service.execute_analysis_run", boom
    )

    assert worker.process_next_job() == run_id
