import logging
from types import SimpleNamespace
from uuid import uuid4

from app.services.agent import quality_agent
from app.services.agent.schemas import AIReviewGenerated


class _FakeSettings:
    def __init__(self, openai_api_key=None, openai_model="gpt-4.1-mini"):
        self.openai_api_key = openai_api_key
        self.openai_model = openai_model


def _fake_run():
    return SimpleNamespace(id=uuid4())


def _stub_chat_openai(monkeypatch, invoke_result):
    class FakeStructuredLLM:
        def invoke(self, messages):
            return invoke_result

    class FakeChatOpenAI:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

        def with_structured_output(self, schema):
            assert schema is AIReviewGenerated
            return FakeStructuredLLM()

    monkeypatch.setattr("langchain_openai.ChatOpenAI", FakeChatOpenAI)


def test_generate_ai_review_snapshot_skips_without_api_key(monkeypatch, caplog):
    monkeypatch.setattr(
        quality_agent, "get_settings", lambda: _FakeSettings(openai_api_key=None)
    )

    with caplog.at_level(logging.INFO, logger="ai-review"):
        result = quality_agent.generate_ai_review_snapshot(analysis_run=_fake_run())

    assert result == {"status": "skipped", "reason": "openai_api_key_missing"}
    assert "OPENAI_API_KEY is not configured" in caplog.text


def test_generate_ai_review_snapshot_returns_model_instance_result(monkeypatch, caplog):
    settings = _FakeSettings(openai_api_key="sk-test", openai_model="gpt-4.1-mini")
    monkeypatch.setattr(quality_agent, "get_settings", lambda: settings)
    monkeypatch.setattr(quality_agent, "build_ai_review_input", lambda run: {"ok": True})
    generated = AIReviewGenerated(
        score=82,
        summary="Looks fine.",
        risk_level="low",
        coverage_assessment="ok",
        security_assessment="ok",
        technical_debt_assessment="ok",
    )
    _stub_chat_openai(monkeypatch, generated)

    with caplog.at_level(logging.INFO, logger="ai-review"):
        result = quality_agent.generate_ai_review_snapshot(analysis_run=_fake_run())

    assert result["status"] == "generated"
    assert result["model"] == "gpt-4.1-mini"
    assert result["score"] == 82
    assert "AI review generated for run" in caplog.text
    assert "score=82" in caplog.text


def test_generate_ai_review_snapshot_validates_raw_dict_result(monkeypatch):
    settings = _FakeSettings(openai_api_key="sk-test")
    monkeypatch.setattr(quality_agent, "get_settings", lambda: settings)
    monkeypatch.setattr(quality_agent, "build_ai_review_input", lambda run: {"ok": True})
    raw_result = {
        "score": 40,
        "summary": "Needs work.",
        "risk_level": "high",
        "coverage_assessment": "low",
        "security_assessment": "flagged",
        "technical_debt_assessment": "high",
    }
    _stub_chat_openai(monkeypatch, raw_result)

    result = quality_agent.generate_ai_review_snapshot(analysis_run=_fake_run())

    assert result["status"] == "generated"
    assert result["risk_level"] == "high"
    assert result["score"] == 40


def test_generate_ai_review_snapshot_logs_and_returns_error_on_exception(
    monkeypatch, caplog
):
    settings = _FakeSettings(openai_api_key="sk-test")
    monkeypatch.setattr(quality_agent, "get_settings", lambda: settings)

    def boom(run):
        raise RuntimeError("network exploded")

    monkeypatch.setattr(quality_agent, "build_ai_review_input", boom)

    with caplog.at_level(logging.ERROR, logger="ai-review"):
        result = quality_agent.generate_ai_review_snapshot(analysis_run=_fake_run())

    assert result == {
        "status": "error",
        "reason": "ai_review_failed",
        "message": "AI review could not be generated.",
    }
    assert "AI review failed for run" in caplog.text
    assert "network exploded" in caplog.text
