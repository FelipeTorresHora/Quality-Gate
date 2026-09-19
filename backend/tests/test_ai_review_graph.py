import json
from pathlib import Path

from app.core.config import Settings
from app.services.agent import graph as graph_module
from app.services.agent import quality_agent
from app.services.agent.prompts import PROMPT_VERSION
from app.services.agent.schemas import AIReviewError, AIReviewGenerated, AIReviewSkipped
from app.services.agent.tools import (
    get_changed_file_hunk,
    get_gate_summary,
    inspect_coverage_numbers,
    list_blocking_findings,
)
from app.services.agent.tracing import build_invocation_config, configure_langsmith_from_settings
from app.services.agent.evaluators import decision_lock, must_cite, no_secrets

DATASET_DIR = Path(__file__).resolve().parents[1] / "evals" / "datasets" / "ai_review"


def _load_example(name: str) -> dict:
    return json.loads((DATASET_DIR / f"{name}.json").read_text())


def test_generate_ai_review_snapshot_skips_without_openai_key(monkeypatch):
    monkeypatch.setattr(
        quality_agent,
        "get_settings",
        lambda: Settings(openai_api_key=None, langsmith_tracing=False),
    )
    snapshot = quality_agent.generate_ai_review_snapshot(analysis_run=object())
    assert snapshot == AIReviewSkipped().model_dump(mode="json")


def test_generate_ai_review_snapshot_returns_error_when_graph_raises(monkeypatch):
    monkeypatch.setattr(
        quality_agent,
        "get_settings",
        lambda: Settings(openai_api_key="sk-test-key", langsmith_tracing=False),
    )

    def boom():
        raise RuntimeError("llm down")

    monkeypatch.setattr(graph_module, "compiled_review_graph", boom)
    run = _FakeRun(decision="fail")
    original_decision = run.decision
    snapshot = quality_agent.generate_ai_review_snapshot(analysis_run=run)
    assert snapshot["status"] == "error"
    assert snapshot["reason"] == "ai_review_failed"
    assert run.decision is original_decision


class _FakeRun:
    def __init__(self, decision="fail"):
        from types import SimpleNamespace
        from uuid import uuid4

        from app.models.enums import AnalysisRunStatus, GateDecision

        self.id = uuid4()
        self.pr_number = 22
        self.head_sha = "bbb222"
        self.status = AnalysisRunStatus.COMPLETED
        self.decision = GateDecision.FAIL if decision == "fail" else GateDecision.PASS
        self.diff_snapshot = ""
        self.diff_truncated = False
        self.pull_request_snapshot_json = {}
        self.changed_files_snapshot_json = []
        self.coverage_result_json = {}
        self.security_result_json = {}
        self.technical_debt_result_json = {}
        self.findings = []
        self.repository = SimpleNamespace(
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
        )


def test_graph_fail_coverage_passes_decision_lock_and_must_cite(monkeypatch):
    example = _load_example("fail_coverage")

    def fake_draft(state):
        return {
            "draft": AIReviewGenerated(
                score=38,
                summary="Gate Decision is fail because Total coverage is below policy at 62%.",
                risk_level="high",
                blocking_reasons=["Total coverage is below policy"],
                suggestions=["Add tests for app/service.py."],
                coverage_assessment="Coverage 62% is below 80%.",
                security_assessment="Security passed.",
                technical_debt_assessment="Technical debt passed.",
            )
        }

    monkeypatch.setattr(graph_module, "draft", fake_draft)
    compiled = graph_module.build_graph().compile()
    result = compiled.invoke(
        {
            "evidence": example["inputs"],
            "model": "gpt-4.1-mini",
            "prompt_version": PROMPT_VERSION,
        }
    )
    snapshot = result["final_snapshot"]
    assert snapshot["status"] == "generated"
    assert snapshot["prompt_version"] == PROMPT_VERSION
    assert result["validation_errors"] == []
    lock = decision_lock(
        snapshot,
        decision="fail",
        blocking_findings=example["inputs"]["findings"],
    )
    cited = must_cite(snapshot, required=example["outputs"]["must_cite"])
    assert lock["score"] == 1.0
    assert cited["score"] == 1.0
    assert snapshot.get("decision") is None


def test_graph_validation_failure_returns_ai_review_error(monkeypatch):
    example = _load_example("fail_coverage")

    def fake_draft(state):
        return {
            "draft": AIReviewGenerated(
                score=99,
                summary="All gates passed and the quality gate passed.",
                risk_level="low",
                blocking_reasons=[],
                suggestions=["Looks good."],
                coverage_assessment="Coverage is fine.",
                security_assessment="Security is fine.",
                technical_debt_assessment="Debt is fine.",
            )
        }

    monkeypatch.setattr(graph_module, "draft", fake_draft)
    compiled = graph_module.build_graph().compile()
    result = compiled.invoke({"evidence": example["inputs"], "model": "gpt-4.1-mini"})
    assert result["final_snapshot"]["status"] == "error"
    assert result["validation_errors"]


def test_retrieve_tools_are_read_only_over_persisted_evidence():
    example = _load_example("fail_coverage")["inputs"]
    summary = get_gate_summary(example)
    findings = list_blocking_findings(example)
    coverage = inspect_coverage_numbers(example)
    hunk = get_changed_file_hunk(example, "app/service.py")
    assert summary["coverage"]["status"] == "fail"
    assert coverage["pr_coverage"] == 62.0
    assert findings[0]["title"] == "Total coverage is below policy"
    assert hunk["found"] is True
    assert "compute" in hunk["patch"]


def test_tracing_helper_includes_analysis_run_id_without_network():
    example = _load_example("fail_coverage")
    config = build_invocation_config(
        evidence=example["inputs"],
        model="gpt-4.1-mini",
        prompt_version=PROMPT_VERSION,
    )
    assert config["metadata"]["analysis_run_id"] == "00000000-0000-0000-0000-000000000002"
    assert "ai-review" in config["tags"]
    assert "prompt:ai-review-v1" in config["tags"]
    assert "decision:fail" in config["tags"]
    assert config["metadata"]["gate_decision"] == "fail"
    assert config["configurable"]["thread_id"] == "00000000-0000-0000-0000-000000000002"


def test_configure_langsmith_from_settings_copies_env(monkeypatch):
    settings = Settings(
        langsmith_tracing=True,
        langsmith_api_key="ls-test-key",
        langsmith_project="pr-quality-dashboard",
        openai_api_key=None,
    )
    monkeypatch.delenv("LANGSMITH_TRACING", raising=False)
    updates = configure_langsmith_from_settings(settings)
    assert updates["LANGSMITH_TRACING"] == "true"
    assert updates["LANGSMITH_API_KEY"] == "ls-test-key"
    assert updates["LANGSMITH_PROJECT"] == "pr-quality-dashboard"


def test_agent_modules_do_not_write_gate_decision():
    agent_dir = Path(__file__).resolve().parents[1] / "app" / "services" / "agent"
    offenders = []
    for path in agent_dir.glob("*.py"):
        text = path.read_text()
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if "run.decision" in stripped and ("=" in stripped) and not stripped.startswith("decision ="):
                if "run.decision.value" in stripped or "run.decision else" in stripped:
                    continue
                if "run.decision =" in stripped or "analysis_run.decision =" in stripped:
                    offenders.append(f"{path.name}: {stripped}")
    assert offenders == []


def test_error_snapshot_shape_unchanged():
    assert AIReviewError().model_dump(mode="json")["reason"] == "ai_review_failed"
    assert no_secrets({"summary": "clean"})["score"] == 1.0
