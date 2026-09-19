from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from app.services.agent.evaluators import evaluate_review

DATASET_DIR = Path(__file__).resolve().parent / "datasets" / "ai_review"


def _load_examples() -> list[dict]:
    return [json.loads(path.read_text()) for path in sorted(DATASET_DIR.glob("*.json"))]


def _reference_output(example: dict) -> dict:
    decision = example["outputs"]["decision"]
    must_cite = example["outputs"].get("must_cite") or []
    evidence = example["inputs"]
    findings = evidence.get("findings") or []
    blocking = [item.get("title") for item in findings if item.get("blocking") and item.get("title")]
    cited = " ".join(must_cite)
    if decision == "fail":
        summary = f"Gate Decision is fail. {cited}".strip()
        score = 40
        risk = "high"
        coverage = f"Coverage evidence: {cited}" if cited else "Coverage gate failed."
    else:
        summary = "Gate Decision is pass. Configured gates completed without blockers."
        score = 88
        risk = "low"
        coverage = "Coverage completed in pass."
    return {
        "status": "generated",
        "model": "gpt-4.1-mini",
        "generated_at": "2026-09-19T00:00:00Z",
        "score": score,
        "summary": summary,
        "risk_level": risk,
        "blocking_reasons": blocking,
        "suggestions": [f"Address {cited}"] if cited else ["Keep the current coverage policy."],
        "coverage_assessment": coverage,
        "security_assessment": summary if "auth.py" in cited or "github.py" in cited else "Security completed.",
        "technical_debt_assessment": summary if "TODO" in cited or "parser.py" in cited else "Technical debt completed.",
    }


def test_code_evaluators_pass_on_golden_reference_outputs():
    for example in _load_examples():
        results = evaluate_review(
            _reference_output(example),
            evidence=example["inputs"],
            expected=example["outputs"],
        )
        failed = [item for item in results if item["score"] < 1]
        assert not failed, f"{example['id']}: {failed}"


@pytest.mark.skipif(
    not os.environ.get("OPENAI_API_KEY") or not os.environ.get("LANGSMITH_API_KEY"),
    reason="live LangSmith evals require OPENAI_API_KEY and LANGSMITH_API_KEY",
)
def test_live_langsmith_eval_optional():
    pytest.skip("Nightly live graph eval is opt-in via keys; code evaluators run locally.")
