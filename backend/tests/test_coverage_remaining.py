import json
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from uuid import UUID, uuid4

import httpx
import jwt
import pytest
from fastapi import Response
from pydantic import ValidationError
from starlette.requests import Request

from app.core.config import (
    Settings,
    get_settings,
    validate_runtime_security_settings,
)
from app.core.errors import AppError
from app.models.analysis_run import AnalysisRun
from app.models.enums import AnalysisRunStatus, AnalysisTriggerSource, GateDecision
from app.models.repository import Repository
from app.models.user import User
from app.schemas.coverage_execution_config import CoverageExecutionConfigUpdate
from app.schemas.repository import RepositoryCreate
from app.services.agent import graph as graph_module
from app.services.agent import quality_agent
from app.services.agent.evaluators import (
    allowed_file_paths,
    decision_lock,
    evaluate_review,
    schema_ok,
    score_alignment,
)
from app.services.agent.schemas import AIReviewGenerated, AIReviewError, AIReviewSkipped
from app.services.agent.tools import (
    collect_tool_results,
    get_changed_file_hunk,
    invoke_review_tools,
    list_blocking_findings,
)
from app.services.agent.tracing import tracing_enabled
from app.services.coverage_parsers.types import CoverageFile, calculate_total
from app.db.session import SessionLocal
from app.services import github_webhook_service, runtime_cache_service, session_service
from app.services.github_service import GitHubClient
from app.services.gates import coverage_gate, technical_debt_gate
from app.services.report_service import build_final_report, build_github_comment_body
from app import worker


EVIDENCE = {
    "findings": [
        {
            "category": "coverage",
            "severity": "high",
            "file_path": "app/a.py",
            "line_number": 1,
            "title": "Low coverage",
            "description": "Coverage low",
            "blocking": True,
        },
        {
            "category": "coverage",
            "severity": "low",
            "file_path": "app/b.py",
            "title": "Info",
            "blocking": False,
        },
    ],
    "changed_files": [
        {"filename": "app/a.py", "patch": "+code"},
        "app/legacy.py",
    ],
    "gate_results": {
        "coverage": {
            "status": "fail",
            "pr_coverage": 50.0,
            "warnings": ["unmatched file"],
        }
    },
}


def test_require_csrf_skips_when_session_cookie_is_invalid(client):
    client.cookies.set("qg_session", "not-a-valid-jwt")
    client.cookies.set("qg_csrf", "csrf-value")

    response = client.post("/api/auth/logout")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_list_repositories_returns_cached_payload(client, repository, monkeypatch):
    monkeypatch.setattr(
        "app.api.routes_repositories.runtime_cache_service.get_json",
        lambda key: None,
    )
    cached = client.get("/api/repositories").json()
    monkeypatch.setattr(
        "app.api.routes_repositories.runtime_cache_service.get_json",
        lambda key: cached,
    )
    monkeypatch.setattr(
        "app.services.repository_service.list_repositories_for_user",
        lambda db, user: (_ for _ in ()).throw(AssertionError("cache miss")),
    )

    response = client.get("/api/repositories")

    assert response.status_code == 200
    assert response.json() == cached


def test_get_repository_cache_hit(client, repository, monkeypatch):
    monkeypatch.setattr(
        "app.api.routes_repositories.runtime_cache_service.get_json",
        lambda key: None,
    )
    cached = client.get(f"/api/repositories/{repository['id']}").json()
    monkeypatch.setattr(
        "app.api.routes_repositories.runtime_cache_service.get_json",
        lambda key: cached,
    )
    monkeypatch.setattr(
        "app.services.repository_service.get_repository",
        lambda db, repository_id: (_ for _ in ()).throw(AssertionError("cache miss")),
    )

    response = client.get(f"/api/repositories/{repository['id']}")

    assert response.status_code == 200
    assert response.json() == cached


def test_list_pull_requests_cache_hit(client, repository, monkeypatch):
    from app.services.github_service import GitHubClient

    def fake_list_pull_requests(self, owner, name):
        from app.schemas.github import GitHubPullRequestRead

        return [
            GitHubPullRequestRead(
                number=1,
                title="Cached PR",
                user_login="octocat",
                state="open",
                draft=False,
                head_ref="feature",
                head_sha="abc",
                base_ref="main",
                html_url="https://github.com/o/r/pull/1",
                created_at="2026-06-21T10:00:00Z",
                updated_at="2026-06-21T11:00:00Z",
            )
        ]

    monkeypatch.setattr(
        GitHubClient,
        "list_pull_requests",
        fake_list_pull_requests,
        raising=False,
    )
    monkeypatch.setattr(
        "app.api.routes_repositories.runtime_cache_service.get_json",
        lambda key: None,
    )
    cached = client.get(f"/api/repositories/{repository['id']}/pull-requests").json()
    monkeypatch.setattr(
        "app.api.routes_repositories.runtime_cache_service.get_json",
        lambda key: cached,
    )
    monkeypatch.setattr(
        "app.services.github_service.list_repository_pull_requests",
        lambda db, repository_id: (_ for _ in ()).throw(AssertionError("cache miss")),
    )

    response = client.get(f"/api/repositories/{repository['id']}/pull-requests")

    assert response.status_code == 200
    assert response.json() == cached


def test_list_analysis_runs_cache_hit(client, repository, monkeypatch):
    monkeypatch.setattr(
        "app.api.routes_analysis.runtime_cache_service.get_json",
        lambda key: None,
    )
    cached = client.get(
        f"/api/repositories/{repository['id']}/analysis-runs"
    ).json()
    monkeypatch.setattr(
        "app.api.routes_analysis.runtime_cache_service.get_json",
        lambda key: cached,
    )
    monkeypatch.setattr(
        "app.services.analysis_service.list_analysis_runs",
        lambda db, repository_id: (_ for _ in ()).throw(AssertionError("cache miss")),
    )

    response = client.get(f"/api/repositories/{repository['id']}/analysis-runs")

    assert response.status_code == 200
    assert response.json() == cached


def test_quality_gate_config_cache_hit(client, repository, monkeypatch):
    monkeypatch.setattr(
        "app.api.routes_quality_gate.runtime_cache_service.get_json",
        lambda key: None,
    )
    cached = client.get(
        f"/api/repositories/{repository['id']}/quality-gate-config"
    ).json()
    monkeypatch.setattr(
        "app.api.routes_quality_gate.runtime_cache_service.get_json",
        lambda key: cached,
    )
    monkeypatch.setattr(
        "app.services.quality_gate_service.get_quality_gate_config",
        lambda db, repository_id: (_ for _ in ()).throw(AssertionError("cache miss")),
    )

    response = client.get(
        f"/api/repositories/{repository['id']}/quality-gate-config"
    )

    assert response.status_code == 200
    assert response.json() == cached


def test_coverage_execution_config_cache_hit(client, repository, monkeypatch):
    monkeypatch.setattr(
        "app.api.routes_coverage_execution_config.runtime_cache_service.get_json",
        lambda key: None,
    )
    cached = client.get(
        f"/api/repositories/{repository['id']}/coverage-execution-config"
    ).json()
    monkeypatch.setattr(
        "app.api.routes_coverage_execution_config.runtime_cache_service.get_json",
        lambda key: cached,
    )
    monkeypatch.setattr(
        "app.services.coverage_execution_config_service.get_coverage_execution_config",
        lambda db, repository_id: (_ for _ in ()).throw(AssertionError("cache miss")),
    )

    response = client.get(
        f"/api/repositories/{repository['id']}/coverage-execution-config"
    )

    assert response.status_code == 200
    assert response.json() == cached


def test_readiness_returns_503_when_github_app_check_fails(client, monkeypatch):
    from app.api import routes_health

    class ErrorResponse:
        is_error = True

    monkeypatch.setattr(
        routes_health.github_app_auth_service,
        "generate_app_jwt",
        lambda: "jwt",
    )
    monkeypatch.setattr(routes_health.httpx, "get", lambda *_, **__: ErrorResponse())

    response = client.get("/health/readiness")

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "github_app_credentials_invalid"


def test_settings_normalized_database_url_variants():
    assert (
        Settings(database_url="postgres://u:p@host/db").normalized_database_url()
        == "postgresql+psycopg://u:p@host/db"
    )
    assert (
        Settings(database_url="postgresql://u:p@host/db").normalized_database_url()
        == "postgresql+psycopg://u:p@host/db"
    )
    assert Settings(database_url="postgresql+psycopg://x").normalized_database_url() == (
        "postgresql+psycopg://x"
    )


def test_settings_infer_vercel_skips_non_dict_and_existing_app_env():
    assert Settings.infer_vercel_environment("not-a-dict") == "not-a-dict"
    values = Settings.infer_vercel_environment({"app_env": "staging", "other": 1})
    assert values["app_env"] == "staging"


def test_validate_runtime_security_https_requires_secure_cookie():
    settings = Settings(
        app_env="production",
        session_secret="x" * 32,
        frontend_origin="https://app.example.com",
        session_cookie_secure=False,
        token_encryption_key="enc-key",
    )
    with pytest.raises(RuntimeError, match="SESSION_COOKIE_SECURE"):
        validate_runtime_security_settings(settings)


def test_validate_runtime_security_requires_token_encryption_key():
    settings = Settings(
        app_env="production",
        session_secret="x" * 32,
        token_encryption_key=None,
    )
    with pytest.raises(RuntimeError, match="TOKEN_ENCRYPTION_KEY"):
        validate_runtime_security_settings(settings)


def test_get_settings_uses_default_env_file(monkeypatch):
    monkeypatch.delenv("PR_QUALITY_ENV_FILE", raising=False)
    get_settings.cache_clear()
    settings = get_settings()
    assert settings.app_name == "PR Quality Gate Dashboard"
    get_settings.cache_clear()


def test_repository_create_default_full_name():
    payload = RepositoryCreate(owner="octo", name="repo")
    assert payload.full_name == "octo/repo"


def test_coverage_execution_config_rejects_blank_fields():
    with pytest.raises(ValidationError):
        CoverageExecutionConfigUpdate(working_directory="   ")
    with pytest.raises(ValidationError):
        CoverageExecutionConfigUpdate(report_path="  ")


def test_list_blocking_findings_skips_non_blocking():
    assert len(list_blocking_findings(EVIDENCE)) == 1


def test_get_changed_file_hunk_not_found():
    result = get_changed_file_hunk(EVIDENCE, "missing.py")
    assert result == {"filename": "missing.py", "found": False, "patch": ""}


def test_collect_tool_results_dedupes_paths_and_falls_back_to_first_file():
    results = collect_tool_results(EVIDENCE)
    assert results["list_blocking_findings"]
    hunks = results["get_changed_file_hunk"]
    assert len(hunks) == 1
    assert hunks[0]["filename"] == "app/a.py"

    evidence_no_blocking = {
        **EVIDENCE,
        "findings": [],
    }
    fallback = collect_tool_results(evidence_no_blocking)
    assert fallback["get_changed_file_hunk"][0]["filename"] == "app/a.py"


def test_invoke_review_tools_skips_duplicate_paths():
    results = invoke_review_tools(EVIDENCE)
    assert len(results["get_changed_file_hunk"]) == 1


def test_graph_load_evidence_from_analysis_run():
    run = _fake_analysis_run()
    state = graph_module.load_evidence({"analysis_run": run, "evidence": {}})
    assert state["analysis_run"] is None
    assert state["evidence"]["analysis_run"]["decision"] == "fail"
    assert state["run_id"] == str(run.id)


def test_graph_validate_missing_draft_and_emit_fallback():
    validated = graph_module.validate({"draft": None})
    assert validated["validation_errors"] == ["draft is missing"]
    assert validated["final_snapshot"]["status"] == "error"

    emitted = graph_module.emit({})
    assert emitted["final_snapshot"]["status"] == "error"
    assert graph_module.emit({"final_snapshot": {"status": "generated"}}) == {}


def test_graph_draft_accepts_structured_and_dict_results(monkeypatch):
    generated = AIReviewGenerated(
        score=55,
        summary="Gate Decision is fail because coverage is low.",
        risk_level="high",
        blocking_reasons=["Low coverage"],
        suggestions=["Add tests."],
        coverage_assessment="Low.",
        security_assessment="Fine.",
        technical_debt_assessment="Fine.",
    )

    class FakeStructured:
        def invoke(self, messages):
            return generated

    class FakeLLM:
        def with_structured_output(self, schema):
            return FakeStructured()

    monkeypatch.setattr("langchain_openai.ChatOpenAI", lambda **kwargs: FakeLLM())
    draft_result = graph_module.draft(
        {
            "decision": "fail",
            "evidence": EVIDENCE,
            "tool_results": {},
            "model": "gpt-test",
        }
    )
    assert draft_result["draft"].score == 55

    class DictStructured:
        def invoke(self, messages):
            return generated.model_dump()

    class DictLLM:
        def with_structured_output(self, schema):
            return DictStructured()

    monkeypatch.setattr("langchain_openai.ChatOpenAI", lambda **kwargs: DictLLM())
    dict_draft = graph_module.draft(
        {"decision": "fail", "evidence": EVIDENCE, "tool_results": {}}
    )
    assert dict_draft["draft"].summary.startswith("Gate Decision")


def test_compiled_review_graph_is_cached():
    graph_module.compiled_review_graph.cache_clear()
    first = graph_module.compiled_review_graph()
    second = graph_module.compiled_review_graph()
    assert first is second
    graph_module.compiled_review_graph.cache_clear()


def test_schema_ok_and_decision_lock_pass_branch():
    bad = schema_ok({"status": "generated", "score": "not-int"})
    assert bad["score"] == 0.0

    output = {
        "score": 80,
        "summary": "Gate Decision is pass and policies were met.",
        "risk_level": "low",
        "blocking_reasons": [],
        "suggestions": [],
        "coverage_assessment": "Good.",
        "security_assessment": "Good.",
        "technical_debt_assessment": "Good.",
    }
    locked = decision_lock(output, decision="pass", blocking_findings=[])
    assert locked["score"] == 1.0
    assert score_alignment({"score": "bad"}, decision="fail")["score"] == 0.0


def test_allowed_file_paths_includes_string_changed_files():
    paths = allowed_file_paths(EVIDENCE)
    assert "app/legacy.py" in paths


def test_evaluate_review_runs_optional_evaluators():
    output = {
        "status": "generated",
        "score": 40,
        "summary": "Gate Decision is fail because Low coverage at 50%.",
        "risk_level": "high",
        "blocking_reasons": ["Low coverage"],
        "suggestions": ["Add tests for app/a.py."],
        "coverage_assessment": "50% vs policy.",
        "security_assessment": "Pass.",
        "technical_debt_assessment": "Pass.",
    }
    results = evaluate_review(
        output,
        evidence=EVIDENCE,
        expected={
            "decision": "fail",
            "must_cite": ["50"],
            "forbidden_substrings": ["INVENTED_SECRET"],
        },
    )
    keys = {item["key"] for item in results}
    assert "must_cite" in keys
    assert "forbidden_substrings" in keys


def test_tracing_enabled_requires_api_key():
    assert tracing_enabled(Settings(langsmith_tracing=True, langsmith_api_key=None)) is False
    assert (
        tracing_enabled(Settings(langsmith_tracing=True, langsmith_api_key="ls-key"))
        is True
    )


def test_generate_ai_review_snapshot_success_and_fallback(monkeypatch):
    monkeypatch.setattr(
        quality_agent,
        "get_settings",
        lambda: Settings(openai_api_key="sk-test", langsmith_tracing=False),
    )
    generated = AIReviewGenerated(
        score=70,
        summary="Gate Decision is pass.",
        risk_level="low",
        blocking_reasons=[],
        suggestions=[],
        coverage_assessment="Ok.",
        security_assessment="Ok.",
        technical_debt_assessment="Ok.",
    ).model_dump(mode="json")
    generated["status"] = "generated"

    class FakeGraph:
        def invoke(self, state, config=None):
            return {"final_snapshot": generated}

    monkeypatch.setattr(
        graph_module,
        "compiled_review_graph",
        lambda: FakeGraph(),
    )
    snapshot = quality_agent.generate_ai_review_snapshot(analysis_run=_fake_analysis_run())
    assert snapshot["status"] == "generated"

    class BadGraph:
        def invoke(self, state, config=None):
            return {"final_snapshot": {"status": "weird"}}

    monkeypatch.setattr(graph_module, "compiled_review_graph", lambda: BadGraph())
    fallback = quality_agent.generate_ai_review_snapshot(analysis_run=_fake_analysis_run())
    assert fallback["status"] == "error"


def test_coverage_file_and_calculate_total_edge_cases():
    assert CoverageFile(covered=0, total=0).percentage == 0
    assert calculate_total({}) == 0
    total = calculate_total({"a": CoverageFile(1, 2), "b": CoverageFile(1, 2)})
    assert total == 50.0


def test_coverage_gate_is_source_file_branches():
    assert coverage_gate.is_source_file("src/app.py", "python")
    assert not coverage_gate.is_source_file("src/test_app.py", "python")
    assert coverage_gate.is_source_file("src/app.ts", "typescript")
    assert not coverage_gate.is_source_file("src/app.test.ts", "typescript")
    assert coverage_gate.is_source_file("src/app.js", "javascript")
    assert coverage_gate.is_source_file("pkg/main.go", "go")
    assert not coverage_gate.is_source_file("pkg/main_test.go", "go")
    assert not coverage_gate.is_source_file("node_modules/pkg/index.js", "javascript")


def test_technical_debt_gate_helper_paths(tmp_path):
    todos = technical_debt_gate.detect_new_todos(
        [{"filename": "src/a.py", "patch": "@@ +1,1 @@\n+# TODO: fix\n"}],
        language="python",
        fail_on_new_todo=True,
    )
    assert todos
    assert technical_debt_gate.validate_diff_evidence([], None) is not None
    module = tmp_path / "a.py"
    module.write_text(
        "def long_function():\n" + "    x = 1\n" * 40 + "\n",
        encoding="utf-8",
    )
    findings = technical_debt_gate.analyze_python_file(
        module,
        display_path="a.py",
        max_function_lines=10,
        max_complexity=1,
    )
    assert findings
    brace_file = tmp_path / "b.ts"
    brace_file.write_text(
        "function longFn() {\n" + "  console.log(1);\n" * 40 + "}\n",
        encoding="utf-8",
    )
    brace_findings = technical_debt_gate.analyze_brace_language_file(
        brace_file,
        display_path="b.ts",
        max_function_lines=10,
        language="typescript",
    )
    assert brace_findings


def test_report_service_skipped_and_error_ai_review_paths():
    run = SimpleNamespace(
        status=AnalysisRunStatus.COMPLETED,
        decision=GateDecision.PASS,
        score=90,
        coverage_result_json={"status": "pass"},
        security_result_json={"status": "pass"},
        technical_debt_result_json={"status": "pass"},
        findings=[],
    )
    skipped = build_final_report(run, {"status": "skipped"})
    assert "skipped" in skipped.lower()
    error_review = build_final_report(run, {"status": "error"})
    assert "could not be generated" in error_review
    no_decision = SimpleNamespace(
        status=AnalysisRunStatus.COMPLETED,
        decision=None,
        score=None,
        coverage_result_json={},
        security_result_json={},
        technical_debt_result_json={},
        findings=[],
    )
    report = build_final_report(no_decision, {})
    assert "No Gate Decision" in report


def test_build_github_comment_body_uses_existing_markdown(reset_database, db_session):
    repo = Repository(
        owner="o",
        name="r",
        full_name="o/r",
        default_branch="main",
    )
    db_session.add(repo)
    db_session.flush()
    run = AnalysisRun(
        repository_id=repo.id,
        pr_number=1,
        head_sha="sha",
        status=AnalysisRunStatus.COMPLETED,
        decision=GateDecision.PASS,
        trigger_source=AnalysisTriggerSource.MANUAL,
        final_report_markdown="# Cached report\n",
        ai_review_json={},
    )
    db_session.add(run)
    db_session.commit()
    body = build_github_comment_body(run)
    assert "# Cached report" in body
    assert str(run.id) in body


def test_github_client_requires_token_and_maps_endpoints(monkeypatch):
    with pytest.raises(AppError) as exc:
        GitHubClient(None).get_repository("o", "r")
    assert exc.value.code == "github_token_missing"

    def fake_request(method, url, **kwargs):
        request = httpx.Request(method, url)
        if method == "GET" and url.endswith("/repos/o/r"):
            return httpx.Response(200, json={"full_name": "o/r"}, request=request)
        if method == "GET" and "/issues/3/comments" in url:
            return httpx.Response(200, json=[{"id": 1}], request=request)
        if method == "POST" and "/issues/3/comments" in url:
            return httpx.Response(201, json={"id": 2}, request=request)
        if method == "PATCH" and "/issues/comments/9" in url:
            return httpx.Response(200, json={"id": 9}, request=request)
        if method == "POST" and "/statuses/sha1" in url:
            return httpx.Response(201, json={"state": "success"}, request=request)
        raise AssertionError(f"unexpected {method} {url}")

    monkeypatch.setattr("app.services.github_service.httpx.get", lambda url, **kw: fake_request("GET", url, **kw))
    monkeypatch.setattr("app.services.github_service.httpx.post", lambda url, **kw: fake_request("POST", url, **kw))
    monkeypatch.setattr("app.services.github_service.httpx.patch", lambda url, **kw: fake_request("PATCH", url, **kw))

    client = GitHubClient("token")
    assert client.get_repository("o", "r")["full_name"] == "o/r"
    assert client.list_issue_comments("o", "r", 3) == [{"id": 1}]
    assert client.create_issue_comment("o", "r", 3, "hi")["id"] == 2
    assert client.update_issue_comment("o", "r", 9, "edit")["id"] == 9
    assert client.create_commit_status(
        "o", "r", "sha1", "success", "ctx", "desc", target_url="https://x"
    )["state"] == "success"


def test_session_service_malformed_payload_and_csrf(reset_database, db_session, monkeypatch):
    user = User(github_user_id=99, github_login="bad-payload")
    db_session.add(user)
    db_session.commit()
    created = session_service.create_session(db_session, user)
    token = jwt.decode(
        created.cookie_value,
        get_settings().session_secret,
        algorithms=["HS256"],
    )
    token.pop("github_user_id")
    bad_cookie = jwt.encode(token, get_settings().session_secret, algorithm="HS256")
    assert session_service.get_user_for_session(bad_cookie, db_session) is None
    assert session_service.validate_csrf_token(created.cookie_value, None) is False
    session_service.revoke_session(db_session, "not-a-session")
    response = Response()
    session_service.clear_session_cookies(response)


def test_runtime_cache_get_cache_success_path(monkeypatch):
    runtime_cache_service._get_cache.cache_clear()

    class WorkingCache:
        namespace = "quality-gate"

        def __init__(self, namespace):
            self.namespace = namespace

    import sys
    from types import ModuleType

    fake_vercel = ModuleType("vercel")
    fake_functions = ModuleType("vercel.functions")
    fake_functions.RuntimeCache = WorkingCache
    fake_vercel.functions = fake_functions
    monkeypatch.setitem(sys.modules, "vercel", fake_vercel)
    monkeypatch.setitem(sys.modules, "vercel.functions", fake_functions)
    monkeypatch.setattr(
        runtime_cache_service,
        "get_settings",
        lambda: Settings(runtime_cache_enabled=True),
    )
    cache = runtime_cache_service._get_cache()
    assert isinstance(cache, WorkingCache)
    runtime_cache_service._get_cache.cache_clear()


def test_worker_run_forever_sleeps_when_idle(monkeypatch):
    calls = {"sleep": 0, "process": 0}

    def fake_process():
        calls["process"] += 1
        return None

    def fake_sleep(seconds):
        calls["sleep"] += 1
        raise KeyboardInterrupt

    monkeypatch.setattr(worker, "process_next_job", fake_process)
    monkeypatch.setattr(worker.time, "sleep", fake_sleep)

    with pytest.raises(KeyboardInterrupt):
        worker.run_forever(poll_seconds=0.01)

    assert calls["process"] == 1
    assert calls["sleep"] == 1


def test_webhook_installation_branches(reset_database, db_session, monkeypatch):
    user = User(github_user_id=555, github_login="sender")
    db_session.add(user)
    db_session.commit()
    calls = {"deactivate": [], "sync": [], "remove": []}
    monkeypatch.setattr(
        "app.services.github_webhook_service.github_installation_service.deactivate_installation",
        lambda db, installation_id, **kwargs: calls["deactivate"].append(
            (installation_id, kwargs)
        ),
    )
    monkeypatch.setattr(
        "app.services.github_webhook_service.github_installation_service.sync_installation_payload",
        lambda db, **kwargs: calls["sync"].append(kwargs.get("replace_repositories")),
    )
    monkeypatch.setattr(
        "app.services.github_webhook_service.github_installation_service.remove_installation_repositories",
        lambda db, installation_id, removed: calls["remove"].append(
            (installation_id, removed)
        ),
    )

    github_webhook_service._process_installation_event(db_session, "installation", {})
    github_webhook_service._process_installation_event(
        db_session,
        "installation",
        {"action": "suspend", "installation": {"id": 10}},
    )
    github_webhook_service._process_installation_event(
        db_session,
        "installation",
        {"action": "deleted", "installation": {"id": 11}},
    )
    github_webhook_service._process_installation_event(
        db_session,
        "installation",
        {
            "action": "created",
            "installation": {"id": 12},
            "repositories": [],
            "sender": {"id": 555},
        },
    )
    github_webhook_service._process_installation_event(
        db_session,
        "installation_repositories",
        {
            "installation": {"id": 13},
            "repositories_added": [{"id": 1, "full_name": "o/r"}],
            "repositories_removed": [{"id": 2}],
            "sender": {"id": 555},
        },
    )

    assert calls["deactivate"]
    assert calls["sync"] == [True, False]
    assert calls["remove"] == [(13, {2})]


def test_webhook_parse_payload_rejects_non_object():
    with pytest.raises(AppError) as exc:
        github_webhook_service._parse_payload(json.dumps([1, 2]).encode())
    assert exc.value.code == "github_webhook_payload_invalid"


def test_webhook_ignores_pull_request_without_repository_name(
    reset_database, db_session, monkeypatch
):
    monkeypatch.setenv("GITHUB_WEBHOOK_SECRET", "secret")
    get_settings.cache_clear()
    monkeypatch.setattr(
        github_webhook_service,
        "_has_valid_signature",
        lambda body, secret, signature_header: True,
    )
    result = github_webhook_service.process_github_webhook(
        db_session,
        json.dumps(
            {
                "action": "opened",
                "repository": {},
                "pull_request": {"number": 1, "state": "open", "draft": False},
            }
        ).encode(),
        "pull_request",
        "sha256=x",
    )
    assert result.reason == "unknown_repository"
    get_settings.cache_clear()


def test_get_analysis_run_not_found(reset_database, db_session):
    from app.services import analysis_service

    with pytest.raises(AppError) as exc:
        analysis_service.get_analysis_run(db_session, uuid4())
    assert exc.value.code == "analysis_run_not_found"


def test_invoke_review_tools_skips_empty_paths_and_duplicates():
    evidence = {
        "findings": [
            {
                "blocking": True,
                "file_path": None,
                "title": "No path",
            },
            {
                "blocking": True,
                "file_path": "app/a.py",
                "title": "One",
            },
            {
                "blocking": True,
                "file_path": "app/a.py",
                "title": "Duplicate",
            },
        ],
        "changed_files": [{"filename": "app/a.py", "patch": "+x"}],
        "gate_results": {},
    }
    results = invoke_review_tools(evidence)
    assert len(results["get_changed_file_hunk"]) == 1


def test_coverage_gate_requires_base_and_head_sha():
    from app.services.gates.coverage_gate import run_coverage_gate
    from app.services.gates.types import GateResult

    run = SimpleNamespace(
        head_sha="head",
        pull_request_snapshot_json={},
        changed_files_snapshot_json=[],
    )

    result = run_coverage_gate(
        analysis_run=run,
        quality_config=SimpleNamespace(max_coverage_drop=5),
        coverage_config=SimpleNamespace(language=SimpleNamespace(value="python")),
        evidence_workspace=SimpleNamespace(),
    )

    assert isinstance(result, GateResult)
    assert result.snapshot["status"] == "error"


def test_analysis_execution_handles_unexpected_exception(
    repository, reset_database, monkeypatch
):
    from app.services import analysis_execution_service

    run_id = _insert_pending_run(repository["id"])
    monkeypatch.setattr(
        analysis_execution_service,
        "_run_pipeline",
        lambda db, run, token: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    with SessionLocal() as db:
        finished = analysis_execution_service.execute_analysis_run(db, run_id)
        assert finished.status == AnalysisRunStatus.ERROR
        assert "Unexpected analysis failure" in (finished.error_message or "")


def test_analysis_service_reuses_existing_run_on_integrity_error(
    reset_database, db_session, repository
):
    from app.schemas.github import PullRequestContextRead
    from app.services import analysis_service

    context = PullRequestContextRead.model_validate(
        {
            "pull_request": {
                "number": 9,
                "title": "Dup",
                "body": None,
                "state": "open",
                "draft": False,
                "author_login": "octocat",
                "html_url": "https://github.com/o/r/pull/9",
                "base_ref": "main",
                "head_ref": "feature",
                "head_sha": "dup-sha",
                "base_sha": "base",
                "created_at": "2026-06-30T00:00:00Z",
                "updated_at": "2026-06-30T00:00:00Z",
            },
            "changed_files": [],
            "diff_snapshot": "diff",
            "diff_truncated": False,
        }
    )
    first = analysis_service.create_or_reuse_manual_analysis_run(
        db_session, UUID(repository["id"]), context
    )
    second = analysis_service.create_or_reuse_manual_analysis_run(
        db_session, UUID(repository["id"]), context
    )
    assert first.id == second.id


def test_github_installation_noops(reset_database, db_session):
    from app.services import github_installation_service

    github_installation_service.deactivate_installation(db_session, 99999)
    github_installation_service.remove_installation_repositories(db_session, 99999, set())
    user = User(github_user_id=1, github_login="solo")
    db_session.add(user)
    db_session.commit()
    github_installation_service.sync_user_installations(db_session, user)


def test_install_url_missing_slug_returns_503(client, monkeypatch):
    monkeypatch.delenv("GITHUB_APP_SLUG", raising=False)
    get_settings.cache_clear()
    response = client.get("/api/github/installations/install-url")
    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "github_app_slug_missing"
    get_settings.cache_clear()


def test_github_app_auth_private_key_and_installation_token(monkeypatch):
    from app.services import github_app_auth_service

    monkeypatch.setenv("GITHUB_APP_ID", "123")
    monkeypatch.setenv(
        "GITHUB_APP_PRIVATE_KEY",
        "-----BEGIN RSA PRIVATE KEY-----\nMIIBOgIBAAJBALRiMLAHudeSA/beuE7\n-----END RSA PRIVATE KEY-----",
    )
    get_settings.cache_clear()
    with pytest.raises(AppError):
        github_app_auth_service.generate_app_jwt()

    class FakeResponse:
        is_error = False

        def json(self):
            return {
                "token": "inst-token",
                "expires_at": (datetime.now(UTC) + timedelta(hours=1)).strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                ),
            }

    monkeypatch.setattr(
        github_app_auth_service,
        "generate_app_jwt",
        lambda: "app-jwt",
    )
    monkeypatch.setattr(github_app_auth_service.httpx, "post", lambda *_, **__: FakeResponse())
    github_app_auth_service.INSTALLATION_TOKEN_CACHE.clear()
    installation_id = 424242
    token = github_app_auth_service.generate_installation_token(installation_id)
    assert token == "inst-token"
    cached = github_app_auth_service.generate_installation_token(installation_id)
    assert cached == "inst-token"
    github_app_auth_service.INSTALLATION_TOKEN_CACHE.clear()
    get_settings.cache_clear()


def test_build_final_report_delegates_to_operational_error():
    run = SimpleNamespace(
        status=AnalysisRunStatus.ERROR,
        decision=None,
        error_message="failed",
        coverage_result_json={},
        security_result_json={},
        technical_debt_result_json={},
    )
    report = build_final_report(run, {})
    assert "OPERATIONAL ERROR" in report


def test_decision_lock_requires_blocking_reasons_on_fail():
    output = {
        "score": 30,
        "summary": "Gate Decision is fail because coverage dropped.",
        "risk_level": "high",
        "blocking_reasons": [],
        "suggestions": [],
        "coverage_assessment": "Bad.",
        "security_assessment": "Ok.",
        "technical_debt_assessment": "Ok.",
    }
    result = decision_lock(
        output,
        decision="fail",
        blocking_findings=[{"blocking": True, "title": "Low coverage"}],
    )
    assert result["score"] == 0.0

    pass_fail = decision_lock(
        {
            **output,
            "summary": "Overall gate decision is fail due to coverage.",
            "blocking_reasons": [],
        },
        decision="pass",
        blocking_findings=[],
    )
    assert pass_fail["score"] == 0.0


def test_dashboard_internal_helpers_empty_inputs():
    from app.services import dashboard_service

    assert dashboard_service._publication_flags_by_repository(object(), set()) == {}


def test_webhook_find_user_without_sender(reset_database, db_session):
    assert github_webhook_service._find_webhook_user(db_session, {}) is None


def test_webhook_parse_invalid_json():
    with pytest.raises(AppError):
        github_webhook_service._parse_payload(b"{not-json")


def _insert_pending_run(repository_id: str):
    with SessionLocal() as db:
        run = AnalysisRun(
            repository_id=UUID(repository_id),
            pr_number=42,
            head_sha="head123",
            status=AnalysisRunStatus.PENDING,
            trigger_source=AnalysisTriggerSource.MANUAL,
            pull_request_snapshot_json={"base_sha": "base123", "number": 42},
            changed_files_snapshot_json=[{"filename": "a.py", "patch": "+x"}],
            diff_snapshot="diff",
        )
        db.add(run)
        db.commit()
        return run.id


def _fake_analysis_run():
    from app.models.enums import AnalysisRunStatus, GateDecision

    run = SimpleNamespace(
        id=uuid4(),
        pr_number=22,
        head_sha="bbb222",
        status=AnalysisRunStatus.COMPLETED,
        decision=GateDecision.FAIL,
        diff_snapshot="",
        diff_truncated=False,
        pull_request_snapshot_json={},
        changed_files_snapshot_json=[],
        coverage_result_json={"status": "fail", "pr_coverage": 50},
        security_result_json={"status": "pass"},
        technical_debt_result_json={"status": "pass"},
        findings=[],
        repository=SimpleNamespace(
            owner="octo-org",
            name="quality-api",
            full_name="octo-org/quality-api",
            default_branch="main",
            quality_gate_config=SimpleNamespace(
                min_total_coverage=80,
                max_coverage_drop=5,
                min_changed_files_coverage=80,
                coverage_enabled=True,
                security_fail_on=["high"],
                security_enabled=True,
                max_function_lines=80,
                max_complexity=10,
                fail_on_new_todo=True,
                technical_debt_enabled=True,
                comment_on_github=False,
                publish_github_status=False,
            ),
            coverage_execution_config=SimpleNamespace(
                language=SimpleNamespace(value="python"),
                working_directory=".",
                report_format=SimpleNamespace(value="cobertura_xml"),
            ),
        ),
    )
    return run
