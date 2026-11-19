import json
from types import SimpleNamespace

import pytest

from app.core.config import Settings
from app.core.errors import AppError
from app.models.enums import FindingCategory, FindingSeverity
from app.services.agent import graph as graph_module
from app.services.agent import quality_agent
from app.services.agent.nodes import coverage_ai as coverage_module
from app.services.agent.nodes import security_ai as security_module
from app.services.agent.nodes import technical_debt_ai as debt_module
from app.services.agent.prompts import (
    COVERAGE_AI_SYSTEM_PROMPT,
    REVIEW_BATCH_SYSTEM_PROMPT,
    SECURITY_AI_SYSTEM_PROMPT,
    SYNTHESIZE_SYSTEM_PROMPT,
    TECH_DEBT_AI_SYSTEM_PROMPT,
)
from app.services.agent.schemas import (
    AICoverageReview,
    AIGateFinding,
    AISecurityReview,
    AITechDebtReview,
    BatchReviewOutput,
    InlineComment,
    TriagedAlert,
    parse_ai_review_snapshot,
)
from app.services.gates import coverage_gate

RAW_DIFF = "RAW_DIFF_MARKER\n+secret line that must stay out of synthesize\n"
SETTINGS = Settings(
    openai_api_key="sk-test",
    openai_model="gpt-6-luna",
    langsmith_tracing=False,
    ai_batch_max_chars=8000,
    ai_max_batches=12,
    ai_pillar_max_chars=8000,
)


class FakeChat:
    def __init__(self, **kwargs):
        self.kwargs = kwargs


@pytest.fixture
def graph_cache():
    clear = getattr(graph_module.compiled_review_graph, "cache_clear", None)
    if clear:
        clear()
    yield
    clear = getattr(graph_module.compiled_review_graph, "cache_clear", None)
    if clear:
        clear()


def _comment(path: str, line: int, title: str = "Name") -> InlineComment:
    return InlineComment(
        file_path=path,
        line_number=line,
        title=title,
        body="Use a clearer name.",
        confidence=0.8,
    )


def _finding(category: FindingCategory) -> AIGateFinding:
    return AIGateFinding(
        category=category,
        severity=FindingSeverity.LOW,
        title=f"{category.value} note",
        description="Non-blocking note.",
        confidence=0.5,
    )


def _coverage() -> AICoverageReview:
    return AICoverageReview(
        summary="Coverage is thin on the new branch.",
        coverage_assessment="Changed lines in a.py are uncovered.",
        findings=[
            _finding(FindingCategory.COVERAGE),
            AIGateFinding(
                category=FindingCategory.COVERAGE,
                severity=FindingSeverity.LOW,
                file_path="app/a.py",
                line_number=99,
                title="Wrong line",
                description="This line is not in the batch.",
                confidence=0.2,
            ),
            AIGateFinding(
                category=FindingCategory.COVERAGE,
                severity=FindingSeverity.LOW,
                file_path="other.py",
                line_number=1,
                title="Elsewhere",
                description="File is outside the diff map.",
                confidence=0.2,
            ),
        ],
    )


def _security() -> AISecurityReview:
    return AISecurityReview(
        summary="Scanner alerts were triaged.",
        security_assessment="No confirmed exploit.",
        triaged_alerts=[
            TriagedAlert(
                scanner="semgrep",
                severity=FindingSeverity.LOW,
                title="Hardcoded value",
                description="Test fixture.",
                confidence=0.4,
                disposition="downgrade",
                rationale="The value is a fixture.",
            )
        ],
        findings=[_finding(FindingCategory.SECURITY)],
    )


def _debt() -> AITechDebtReview:
    return AITechDebtReview(
        summary="No design smell.",
        technical_debt_assessment="Functions stay small.",
        findings=[_finding(FindingCategory.TECHNICAL_DEBT)],
    )


class _Slice:
    def __init__(self, batches, skipped=None, truncated=False, total=None, sent=None):
        self.batches = batches
        self.skipped_files = skipped or []
        self.review_truncated = truncated
        self.batches_total = len(batches) if total is None else total
        self.batches_sent = len(batches) if sent is None else sent
        merged: dict[str, list[int]] = {}
        for batch in batches:
            for path, lines in batch["valid_lines_by_file"].items():
                bucket = merged.setdefault(path, [])
                for line in lines:
                    if line not in bucket:
                        bucket.append(line)
        self.valid_lines_by_file = merged
        self.batch_max_chars = 8000
        self.max_batches = 12


def _digest(pillar: str, text: str, mode: str = "hybrid", truncated: bool = False, skipped=None):
    return SimpleNamespace(
        digest={
            "pillar": pillar,
            "mode": mode,
            "deterministic_status": "pass",
            "evidence_text": text,
        },
        review_truncated=truncated,
        skipped_files=skipped or [],
        pillar_max_chars=8000,
    )


def _install(monkeypatch, *, batches, structured, digests=None, uncovered=None, settings=SETTINGS):
    import sys
    from types import ModuleType

    digests = digests or {}
    calls = {"slice": [], "structured": [], "uncovered": [], "lines": [], "digests": []}

    def slice_review_batches(diff_text, *, security_alerts=None, uncovered_lines_by_file=None, max_batch_chars=None, max_batches=None):
        calls["slice"].append(
            {
                "diff_text": diff_text,
                "security_alerts": security_alerts,
                "uncovered_lines_by_file": uncovered_lines_by_file,
                "max_batch_chars": max_batch_chars,
                "max_batches": max_batches,
            }
        )
        return _Slice(batches)

    def valid_lines_for_diff(diff_text):
        calls["lines"].append(diff_text)
        return {"app/a.py": [4]}

    def build_coverage_digest(**kwargs):
        calls["digests"].append(("coverage", kwargs))
        return digests.get(
            "coverage",
            _digest("coverage", "COVERAGE_DIGEST", mode=kwargs.get("mode", "hybrid")),
        )

    def build_security_digest(**kwargs):
        calls["digests"].append(("security", kwargs))
        return digests.get(
            "security",
            _digest("security", "SECURITY_DIGEST", mode=kwargs.get("mode", "hybrid")),
        )

    def build_debt_digest(**kwargs):
        calls["digests"].append(("technical_debt", kwargs))
        return digests.get(
            "technical_debt",
            _digest("technical_debt", "DEBT_DIGEST", mode=kwargs.get("mode", "hybrid")),
        )

    slicer = ModuleType("app.services.agent.context_slicer")
    slicer.slice_review_batches = slice_review_batches
    slicer.valid_lines_for_diff = valid_lines_for_diff
    slicer.build_coverage_digest = build_coverage_digest
    slicer.build_security_digest = build_security_digest
    slicer.build_debt_digest = build_debt_digest
    sys.modules["app.services.agent.context_slicer"] = slicer

    async def ainvoke_structured(llm, schema, messages, max_attempts=2):
        calls["structured"].append(
            {"schema": schema, "messages": messages, "llm": llm, "max_attempts": max_attempts}
        )
        result = structured(schema, messages, llm)
        if isinstance(result, schema):
            return result
        return schema.model_validate(result)

    structured_mod = ModuleType("app.services.agent.structured")
    structured_mod.ainvoke_structured = ainvoke_structured
    sys.modules["app.services.agent.structured"] = structured_mod

    def fake_uncovered(report, changed_files, language, working_directory="."):
        calls["uncovered"].append(
            {
                "report": report,
                "changed_files": changed_files,
                "language": language,
                "working_directory": working_directory,
            }
        )
        return uncovered if uncovered is not None else {"app/a.py": [4]}

    monkeypatch.setattr(coverage_gate, "uncovered_lines_by_file", fake_uncovered, raising=False)
    monkeypatch.setattr(graph_module, "get_settings", lambda: settings)
    monkeypatch.setattr("app.core.config.get_settings", lambda: settings)
    monkeypatch.setattr("langchain_openai.ChatOpenAI", FakeChat)
    return calls


def _batch(batch_id: str, diff: str, lines: list[int] | None = None) -> dict:
    return {
        "batch_id": batch_id,
        "file_paths": ["app/a.py"],
        "diff_text": diff,
        "valid_lines_by_file": {"app/a.py": lines or [4]},
    }


def _state(**overrides):
    evidence = {
        "diff_snapshot": RAW_DIFF,
        "coverage_report": {"files": {}},
        "language": "python",
        "working_directory": "src",
        "coverage_result": {
            "status": "fail",
            "pr_coverage": 62,
            "changed_files_coverage": 40,
            "blocking_reasons": ["below policy"],
        },
        "security_result": {"status": "pass"},
        "technical_debt_result": {"status": "pass", "new_todo_count": 0},
        "security_alerts": [
            {
                "scanner": "semgrep",
                "file_path": "app/a.py",
                "line_number": 4,
                "title": "literal",
                "severity": "low",
            }
        ],
        "debt_findings": [],
        "code_review_enabled": True,
        "coverage_mode": "hybrid",
        "security_mode": "hybrid",
        "technical_debt_mode": "hybrid",
    }
    evidence.update(overrides.pop("evidence", {}))
    payload = {
        "run_id": "run-1",
        "repository_full_name": "octo/quality",
        "pr_number": 7,
        "head_sha": "abc",
        "decision": "fail",
        "model": "gpt-6-luna",
        "prompt_version": "ai-review-v1",
        "changed_files": [{"filename": "app/a.py", "patch": RAW_DIFF}],
        "diff_truncated": False,
        "evidence": evidence,
    }
    payload.update(overrides)
    return payload


def _handler(security_error: bool = False, hallucinate: bool = False, synthesis_error: bool = False):
    def structured(schema, messages, llm):
        assert llm.kwargs == {
            "model": "gpt-6-luna",
            "api_key": "sk-test",
            "temperature": 0,
        }
        name = schema.__name__
        if name == "BatchReviewOutput":
            lines = [4, 99] if hallucinate else [4]
            return BatchReviewOutput(
                batch_id="batch",
                summary="Reviewed the batch.",
                inline_comments=[_comment("app/a.py", line) for line in lines],
            )
        if name == "AICoverageReview":
            return _coverage()
        if name == "AISecurityReview":
            if security_error:
                raise AppError(502, "ai_structured_output_invalid", "security failed")
            return _security()
        if name == "AITechDebtReview":
            return _debt()
        if name == "ReviewSynthesis":
            if synthesis_error:
                raise RuntimeError("synthesis down")
            return schema.model_validate(
                {
                    "score": 42,
                    "summary": "Gate Decision stays fail. Validated review only.",
                    "risk_level": "high",
                    "blocking_reasons": ["Coverage is below policy"],
                    "suggestions": ["Add a test for app/a.py."],
                    "coverage_assessment": "from model",
                    "security_assessment": "from model",
                    "technical_debt_assessment": "from model",
                }
            )
        raise AssertionError(name)

    return structured


def _run(monkeypatch, batches, **handler_kwargs):
    calls = _install(monkeypatch, batches=batches, structured=_handler(**handler_kwargs))
    result = graph_module.compiled_review_graph().invoke(_state())
    return result, calls


def test_prompts_do_not_embed_a_full_diff_payload():
    for prompt in (
        REVIEW_BATCH_SYSTEM_PROMPT,
        COVERAGE_AI_SYSTEM_PROMPT,
        SECURITY_AI_SYSTEM_PROMPT,
        TECH_DEBT_AI_SYSTEM_PROMPT,
        SYNTHESIZE_SYSTEM_PROMPT,
    ):
        assert "diff_snapshot" not in prompt
        assert "changed_files" not in prompt


def test_multi_batch_fan_out_reviews_each_batch_alone(monkeypatch, graph_cache):
    batches = [_batch("batch-1", "BATCH_ONE_DIFF"), _batch("batch-2", "BATCH_TWO_DIFF")]
    result, calls = _run(monkeypatch, batches)
    review_calls = [item for item in calls["structured"] if item["schema"].__name__ == "BatchReviewOutput"]
    assert len(review_calls) == 2
    bodies = ["\n".join(message[1] for message in item["messages"]) for item in review_calls]
    assert any("BATCH_ONE_DIFF" in body and "BATCH_TWO_DIFF" not in body for body in bodies)
    assert any("BATCH_TWO_DIFF" in body and "BATCH_ONE_DIFF" not in body for body in bodies)
    assert calls["slice"][0]["max_batches"] == 12
    assert calls["slice"][0]["diff_text"] == RAW_DIFF
    assert calls["uncovered"][0]["language"] == "python"
    assert calls["uncovered"][0]["working_directory"] == "src"
    snapshot = parse_ai_review_snapshot(result["final_snapshot"])
    assert snapshot.status == "generated"
    assert snapshot.score == 42
    assert {item.batch_id for item in result["batch_reviews"]}


def test_hallucinated_line_is_dropped(monkeypatch, graph_cache):
    result, _calls = _run(monkeypatch, [_batch("batch-1", "BATCH_ONE_DIFF")], hallucinate=True)
    snapshot = parse_ai_review_snapshot(result["final_snapshot"])
    assert [comment.line_number for comment in snapshot.inline_comments] == [4]
    assert all(comment.line_number != 99 for comment in result["inline_comments"])


def test_one_node_failure_keeps_partial_snapshot(monkeypatch, graph_cache):
    result, _calls = _run(monkeypatch, [_batch("batch-1", "BATCH_ONE_DIFF")], security_error=True)
    snapshot = parse_ai_review_snapshot(result["final_snapshot"])
    assert snapshot.status == "partial"
    assert snapshot.reason == "context_budget_exhausted"
    assert snapshot.pillar_insights.coverage is not None
    assert snapshot.pillar_insights.technical_debt is not None
    assert snapshot.pillar_insights.security is None
    assert snapshot.inline_comments
    assert snapshot.context_budget.batches_sent == 1
    assert "security_ai" in snapshot.summary
    statuses = {
        item["node"]: item["status"]
        for item in result["node_outcomes"]
        if item["node"] == "security_ai"
    }
    assert statuses["security_ai"] == "error"


def test_synthesize_review_never_receives_the_raw_diff(monkeypatch, graph_cache):
    seen = {}
    original = graph_module.synthesize_review

    def spy(state):
        seen["state"] = json.dumps(state, default=str)
        return original(state)

    monkeypatch.setattr(graph_module, "synthesize_review", spy)
    graph_module.compiled_review_graph.cache_clear()
    result, calls = _run(monkeypatch, [_batch("batch-1", "SAFE_BATCH_DIFF")])
    synthesis = next(item for item in calls["structured"] if item["schema"].__name__ == "ReviewSynthesis")
    message_text = json.dumps(synthesis["messages"])
    assert "RAW_DIFF_MARKER" not in seen["state"]
    assert "RAW_DIFF_MARKER" not in message_text
    assert SYNTHESIZE_SYSTEM_PROMPT in message_text
    assert "SAFE_BATCH_DIFF" not in message_text
    specialist = [
        item
        for item in calls["structured"]
        if item["schema"].__name__ in {"AICoverageReview", "AISecurityReview", "AITechDebtReview"}
    ]
    assert specialist
    for item in specialist:
        human = item["messages"][1][1]
        assert "RAW_DIFF_MARKER" not in human
        assert len(human) <= 8000
    assert "RAW_DIFF_MARKER" not in json.dumps(result["final_snapshot"])


def test_fan_out_stops_at_twelve_batches(monkeypatch, graph_cache):
    batches = [_batch(f"batch-{index}", f"DIFF_{index}") for index in range(1, 14)]
    result, calls = _run(monkeypatch, batches)
    review_calls = [item for item in calls["structured"] if item["schema"].__name__ == "BatchReviewOutput"]
    assert len(review_calls) == 12
    snapshot = parse_ai_review_snapshot(result["final_snapshot"])
    assert snapshot.status == "partial"
    assert snapshot.context_budget.batches_sent == 12
    assert snapshot.context_budget.batches_total == 13
    assert snapshot.context_budget.review_truncated is True


def test_deterministic_pillar_is_skipped_and_ai_only_still_runs(monkeypatch, graph_cache):
    calls = _install(
        monkeypatch,
        batches=[_batch("batch-1", "SAFE_BATCH_DIFF")],
        structured=_handler(),
    )
    result = graph_module.compiled_review_graph().invoke(
        _state(
            evidence={
                "code_review_enabled": False,
                "coverage_mode": "ai_only",
                "security_mode": "deterministic",
                "technical_debt_mode": "deterministic",
            }
        )
    )
    names = [item["schema"].__name__ for item in calls["structured"]]
    assert "AICoverageReview" in names
    assert "AISecurityReview" not in names
    assert "AITechDebtReview" not in names
    assert "BatchReviewOutput" not in names
    skipped = {
        item["node"]
        for item in result["node_outcomes"]
        if item["status"] == "skipped"
    }
    assert {"review_batch", "security_ai", "technical_debt_ai"} <= skipped
    assert parse_ai_review_snapshot(result["final_snapshot"]).status == "generated"


def test_specialist_digest_is_capped_at_pillar_max(monkeypatch, graph_cache):
    long_text = "Z" * 9000
    calls = _install(
        monkeypatch,
        batches=[],
        structured=_handler(),
        digests={"coverage": _digest("coverage", long_text, mode="ai_only")},
        settings=Settings(
            openai_api_key="sk-test",
            openai_model="gpt-6-luna",
            langsmith_tracing=False,
            ai_pillar_max_chars=8000,
            ai_max_batches=12,
            ai_batch_max_chars=8000,
        ),
    )
    graph_module.compiled_review_graph().invoke(
        _state(
            evidence={
                "code_review_enabled": False,
                "coverage_mode": "ai_only",
                "security_mode": "deterministic",
                "technical_debt_mode": "deterministic",
            }
        )
    )
    coverage_call = next(item for item in calls["structured"] if item["schema"].__name__ == "AICoverageReview")
    assert coverage_call["messages"][1][1] == "Z" * 8000
    assert calls["digests"][0][1]["max_chars"] == 8000


def test_synthesis_failure_still_preserves_other_pillars(monkeypatch, graph_cache):
    result, _calls = _run(
        monkeypatch,
        [_batch("batch-1", "SAFE_BATCH_DIFF")],
        synthesis_error=True,
    )
    snapshot = parse_ai_review_snapshot(result["final_snapshot"])
    assert snapshot.status == "partial"
    assert snapshot.inline_comments
    assert snapshot.pillar_insights.coverage is not None
    assert any(item["node"] == "synthesize_review" and item["status"] == "error" for item in result["node_outcomes"])


def test_all_model_nodes_failing_returns_ai_review_error(monkeypatch, graph_cache):
    def boom(schema, messages, llm):
        raise RuntimeError("down")

    _install(monkeypatch, batches=[_batch("batch-1", "SAFE_BATCH_DIFF")], structured=boom)
    result = graph_module.compiled_review_graph().invoke(_state())
    snapshot = result["final_snapshot"]
    assert snapshot["status"] == "error"
    assert snapshot["reason"] == "ai_review_failed"


def test_duplicate_skipped_files_are_deduped_on_the_budget(monkeypatch, graph_cache):
    calls = _install(
        monkeypatch,
        batches=[_batch("batch-1", "SAFE_BATCH_DIFF")],
        structured=_handler(),
        digests={
            "coverage": _digest("coverage", "COVERAGE_DIGEST", skipped=["dup.py"]),
            "security": _digest("security", "SECURITY_DIGEST", skipped=["dup.py", "other.py"]),
        },
    )

    def slice_with_dup(diff_text, **kwargs):
        calls["slice"].append(kwargs)
        return _Slice([_batch("batch-1", "SAFE_BATCH_DIFF")], skipped=["dup.py", "dup.py"])

    import sys

    sys.modules["app.services.agent.context_slicer"].slice_review_batches = slice_with_dup
    result = graph_module.compiled_review_graph().invoke(_state())
    assert result["final_snapshot"]["context_budget"]["skipped_files"] == ["dup.py", "other.py"]


def test_direct_pillar_nodes_record_their_own_errors():
    import sys
    from types import ModuleType

    structured_mod = ModuleType("app.services.agent.structured")

    async def ainvoke_structured(llm, schema, messages, max_attempts=2):
        raise RuntimeError("pillar down")

    structured_mod.ainvoke_structured = ainvoke_structured
    sys.modules["app.services.agent.structured"] = structured_mod
    for node in (coverage_module.coverage_ai, security_module.security_ai, debt_module.technical_debt_ai):
        failed = node({})
        assert failed["node_outcomes"][0]["status"] == "error"
        assert failed["ai_findings"] == []


def test_prepare_context_accepts_stored_lines_and_object_batches(monkeypatch, graph_cache):
    from app.services.agent.nodes import outcome as node_outcome

    assert node_outcome("review_batch", "ok")["status"] == "completed"
    calls = _install(monkeypatch, batches=[], structured=_handler())

    class _Batch:
        batch_id = "batch-obj"
        file_paths = ["app/a.py"]
        diff_text = "OBJECT_DIFF"
        valid_lines_by_file = {"app/a.py": ["4", "bad", 4]}

    class _Digest:
        pillar = "coverage"
        mode = "nope"
        deterministic_status = None
        evidence_text = "OBJECT_DIGEST"

    def slice_objects(diff_text, **kwargs):
        calls["slice"].append(kwargs)
        sliced = _Slice([])
        sliced.batches = [_Batch()]
        sliced.review_truncated = True
        return sliced

    import sys

    sys.modules["app.services.agent.context_slicer"].slice_review_batches = slice_objects
    sys.modules["app.services.agent.context_slicer"].build_coverage_digest = (
        lambda **kwargs: SimpleNamespace(
            digest=_Digest(),
            review_truncated=True,
            skipped_files=["noise.py"],
            pillar_max_chars=8000,
        )
    )
    sys.modules["app.services.agent.context_slicer"].valid_lines_for_diff = lambda diff_text: None

    result = graph_module.compiled_review_graph().invoke(
        _state(
            diff_truncated=True,
            evidence={
                "diff_snapshot": 5,
                "coverage_report": None,
                "coverage_result": {
                    "pr_coverage": "n/a",
                    "uncovered_lines_by_file": {"": [1], "app/a.py": [4, "x"]},
                },
                "coverage_mode": "nope",
            },
        )
    )
    assert calls["uncovered"] == []
    assert result["final_snapshot"]["status"] in {"generated", "partial"}
    assert graph_module._bounded("nope", 12) == 12
    assert graph_module._bounded(-3, 12) == 0

    def explode(state):
        raise RuntimeError("status")

    monkeypatch.setattr(
        "app.services.agent.nodes.synthesize.review_status",
        explode,
    )
    failed = graph_module.merge_and_validate({"batches": "bad"})
    assert failed["node_outcomes"][0]["status"] == "error"


def test_quality_agent_returns_partial_score_without_writing_decision(monkeypatch, graph_cache):
    monkeypatch.setattr(quality_agent, "get_settings", lambda: SETTINGS)
    partial = {
        "status": "partial",
        "model": "gpt-6-luna",
        "summary": "Kept the other pillars.",
        "score": 55,
        "reason": "context_budget_exhausted",
        "inline_comments": [],
        "pillar_insights": {"coverage": None, "security": None, "technical_debt": None},
        "context_budget": {
            "batches_sent": 1,
            "batches_total": 2,
            "review_truncated": True,
            "skipped_files": [],
        },
    }

    class FakeGraph:
        def invoke(self, state, config=None):
            assert "diff_snapshot" in state["evidence"]
            return {"final_snapshot": partial}

    monkeypatch.setattr(graph_module, "compiled_review_graph", lambda: FakeGraph())
    run = _fake_run()
    decision = run.decision
    snapshot = quality_agent.generate_ai_review_snapshot(analysis_run=run)
    assert snapshot["status"] == "partial"
    assert snapshot["score"] == 55
    assert run.decision is decision


def _fake_run():
    from uuid import uuid4

    from app.models.enums import AnalysisRunStatus, GateDecision

    return SimpleNamespace(
        id=uuid4(),
        pr_number=22,
        head_sha="bbb222",
        status=AnalysisRunStatus.COMPLETED,
        decision=GateDecision.FAIL,
        diff_snapshot="",
        diff_truncated=False,
        pull_request_snapshot_json={},
        changed_files_snapshot_json=[],
        coverage_result_json={"status": "pass"},
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
                code_review_enabled=True,
                coverage_mode="hybrid",
                security_mode="hybrid",
                technical_debt_mode="hybrid",
            ),
            coverage_execution_config=SimpleNamespace(
                language=SimpleNamespace(value="python"),
                working_directory=".",
                report_format=SimpleNamespace(value="cobertura_xml"),
            ),
        ),
    )
