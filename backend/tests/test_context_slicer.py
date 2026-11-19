import asyncio
import json

import pytest
from pydantic import ValidationError

from app.core.errors import AppError
from app.services.agent.context_slicer import (
    build_coverage_digest,
    build_debt_digest,
    build_security_digest,
    slice_review_batches,
    valid_lines_for_diff,
)
from app.services.agent.schemas import BatchReviewOutput
from app.services.agent.structured import ainvoke_structured
from app.services.evidence_redaction_service import REDACTION_MARKER


def _added(path: str, lines: list[str]) -> str:
    body = "\n".join(f"+{line}" for line in lines)
    count = len(lines)
    return "\n".join(
        [
            f"diff --git a/{path} b/{path}",
            "new file mode 100644",
            "--- /dev/null",
            f"+++ b/{path}",
            f"@@ -0,0 +1,{count} @@",
            body,
            "",
        ]
    )


def test_valid_lines_map_right_side_and_skip_deletions():
    diff = "\n".join(
        [
            "diff --git a/src/app.py b/src/app.py",
            "index 111..222 100644",
            "--- a/src/app.py",
            "+++ b/src/app.py",
            "@@ -10,4 +20,5 @@",
            " context",
            "-removed",
            "+added",
            " context",
            " context",
            "@@ -40,2 +50,2 @@",
            " keep",
            "-old",
            "+new",
            "diff --git a/src/other.py b/src/other.py",
            "--- a/src/other.py",
            "+++ b/src/other.py",
            "@@ -1 +1 @@",
            "-old",
            "+fresh",
            "",
        ]
    )

    assert valid_lines_for_diff(diff) == {
        "src/app.py": [20, 21, 22, 23, 50, 51],
        "src/other.py": [1],
    }


def test_slice_prioritizes_alerts_then_uncovered_then_largest_hunks():
    diff = "\n".join(
        [
            _added("plain.py", [f"value_{index} = {index}" for index in range(30)]),
            _added("gap.py", ["missing = True"]),
            _added("auth.py", ["session = True"]),
            _added("small.py", ["n = 1"]),
        ]
    )

    sliced = slice_review_batches(
        diff,
        security_alerts=[{"file_path": "auth.py", "scanner": "semgrep", "title": "session"}],
        uncovered_lines_by_file={"gap.py": [1], "plain.py": []},
        max_batch_chars=8000,
        max_batches=12,
    )

    assert sliced.review_truncated is False
    assert sliced.skipped_files == []
    assert sliced.batches_sent == 1
    assert sliced.batches_total == 1
    assert sliced.batches[0]["file_paths"] == ["auth.py", "gap.py", "plain.py", "small.py"]
    assert sliced.batches[0]["batch_id"] == "batch-1"
    assert sliced.valid_lines_by_file["auth.py"] == [1]
    assert sliced.batch_max_chars == 8000
    assert sliced.max_batches == 12


def test_slice_truncates_extra_batches_and_clips_oversized_files():
    parts = [
        _added("auth.py", ["token = 'kept'"] + [f"a{index} = {index}" for index in range(8)]),
        _added("gap.py", [f"gap_{index} = {index}" for index in range(8)]),
        _added("plain.py", [f"plain_{index} = {index}" for index in range(8)]),
    ]
    lengths = [len(part) for part in parts]
    limit = max(lengths) + 5
    assert all(length + 1 + min(lengths) > limit for length in lengths)

    sliced = slice_review_batches(
        "\n".join(parts),
        security_alerts=[{"filename": "auth.py", "scanner": "bandit", "title": "token"}],
        uncovered_lines_by_file={"gap.py": [2]},
        max_batch_chars=limit,
        max_batches=1,
    )

    assert sliced.review_truncated is True
    assert sliced.batches_sent == 1
    assert sliced.batches_total == 3
    assert sliced.batches[0]["file_paths"] == ["auth.py"]
    assert sliced.skipped_files == ["gap.py", "plain.py"]
    assert len(sliced.batches[0]["diff_text"]) <= limit

    huge = _added("wide.py", [f"line_{index} = {index}" for index in range(40)])
    clipped = slice_review_batches(huge, max_batch_chars=180, max_batches=4)
    assert clipped.review_truncated is True
    assert clipped.batches_sent == 1
    assert len(clipped.batches[0]["diff_text"]) <= 180
    sent_lines = clipped.batches[0]["valid_lines_by_file"]["wide.py"]
    assert sent_lines
    assert sent_lines == list(range(1, len(sent_lines) + 1))
    assert len(sent_lines) < 40
    assert sent_lines == valid_lines_for_diff(clipped.batches[0]["diff_text"])["wide.py"]


def test_slice_drops_noise_files_and_redacts_secrets_before_the_batch():
    secret = "sk-proj-abcdefghijklmnopqrstuvwxyz1234"
    diff = "\n".join(
        [
            _added("src/app.py", [f"API_KEY={secret}", "value = 1"]),
            _added("package-lock.json", ["lock = true"]),
            _added("dist/bundle.js", ["bundle = 1"]),
            _added("node_modules/left-pad/index.js", ["module.exports = 1"]),
            _added("src/app.min.js", ["min = 1"]),
            _added("src/app.js.map", ["map = 1"]),
            _added("src/logo.svg", ["<svg></svg>"]),
            _added("src/logo.png", ["png"]),
            "\n".join(
                [
                    "diff --git a/assets/blob.bin b/assets/blob.bin",
                    "new file mode 100644",
                    "index 0000000..111",
                    "Binary files /dev/null and b/assets/blob.bin differ",
                ]
            ),
        ]
    )

    sliced = slice_review_batches(diff, max_batch_chars=8000, max_batches=12)
    payload = sliced.batches[0]["diff_text"]

    assert sliced.batches[0]["file_paths"] == ["src/app.py"]
    assert sliced.review_truncated is False
    assert secret not in payload
    assert "supersecret" not in payload
    assert REDACTION_MARKER in payload
    assert sliced.skipped_files == [
        "package-lock.json",
        "dist/bundle.js",
        "node_modules/left-pad/index.js",
        "src/app.min.js",
        "src/app.js.map",
        "src/logo.svg",
        "src/logo.png",
        "assets/blob.bin",
    ]
    assert sliced.valid_lines_by_file["src/app.py"] == [1, 2]


def test_pillar_digests_cap_chars_redact_and_keep_relevant_hunks():
    secret = "github_pat_" + ("a" * 24)
    coverage_diff = "\n".join(
        [
            _added("src/app.py", ["covered = True", "API_KEY=" + secret, "gap = None"]),
            _added("src/other.py", ["unused = 1"]),
        ]
    )
    coverage = build_coverage_digest(
        mode="hybrid",
        deterministic_status="fail",
        uncovered_lines_by_file={"src/app.py": [3], "src/other.py": []},
        diff_text=coverage_diff,
        pr_coverage=40,
        changed_files_coverage=10,
        blocking_reasons=["Total coverage is below policy"],
        max_chars=8000,
    )
    assert coverage.digest["pillar"] == "coverage"
    assert coverage.digest["mode"] == "hybrid"
    assert coverage.digest["deterministic_status"] == "fail"
    assert "src/app.py: 3" in coverage.digest["evidence_text"]
    assert "src/other.py" not in coverage.digest["evidence_text"]
    assert secret not in coverage.digest["evidence_text"]
    assert REDACTION_MARKER in coverage.digest["evidence_text"]
    assert coverage.review_truncated is False

    tiny = build_coverage_digest(
        mode="ai_only",
        deterministic_status="fail",
        uncovered_lines_by_file={"src/app.py": [3]},
        diff_text=coverage_diff,
        blocking_reasons=["x" * 500],
        max_chars=120,
    )
    assert tiny.review_truncated is True
    assert len(tiny.digest["evidence_text"]) <= 120
    assert tiny.pillar_max_chars == 120

    security_diff = "\n".join(
        [
            _added("src/auth.py", ["password = 'hunter2'", "return password"]),
            _added("src/db.py", ['cursor.execute("SELECT * FROM users")']),
            _added("src/plain.py", ["return 1"]),
        ]
    )
    security = build_security_digest(
        mode="deterministic",
        deterministic_status="pass",
        diff_text=security_diff,
        alerts=[
            {
                "scanner": "semgrep",
                "file_path": "src/auth.py",
                "line_number": 1,
                "severity": "high",
                "title": "hardcoded password",
            }
        ],
        max_chars=8000,
    )
    evidence = security.digest["evidence_text"]
    assert security.digest["pillar"] == "security"
    assert "semgrep" in evidence
    assert "src/auth.py" in evidence
    assert "cursor.execute" in evidence
    assert "src/plain.py" not in evidence
    assert security.review_truncated is False

    debt = build_debt_digest(
        mode="hybrid",
        deterministic_status="fail",
        findings=[
            {
                "severity": "medium",
                "file_path": "src/plain.py",
                "line_number": 1,
                "title": "New TODO/FIXME marker",
                "description": "TODO added",
            }
        ],
        diff_text=_added("src/plain.py", ["TODO: fix later"]),
        snapshot={"new_todo_count": 1, "blocking_reasons": ["New TODO/FIXME marker"]},
        max_chars=8000,
    )
    assert debt.digest["pillar"] == "technical_debt"
    assert "New TODO/FIXME marker" in debt.digest["evidence_text"]
    assert "TODO: fix later" in debt.digest["evidence_text"]
    assert debt.review_truncated is False


def test_ainvoke_structured_resends_pydantic_error_then_stops():
    class FakeRunnable:
        def __init__(self, failures: int):
            self.failures = failures
            self.calls: list[list] = []

        async def ainvoke(self, messages):
            self.calls.append(messages)
            if len(self.calls) <= self.failures:
                try:
                    BatchReviewOutput.model_validate({"batch_id": "", "summary": "x"})
                except ValidationError as exc:
                    return {"raw": {"content": "{}"}, "parsed": None, "parsing_error": exc}
            return {
                "raw": {"content": "ok"},
                "parsed": BatchReviewOutput(batch_id="batch-1", summary="ok"),
                "parsing_error": None,
            }

    class FakeLLM:
        def __init__(self, failures: int):
            self.runnable = FakeRunnable(failures)
            self.kwargs = None

        def with_structured_output(self, schema, include_raw=False):
            self.kwargs = {"schema": schema, "include_raw": include_raw}
            return self.runnable

    llm = FakeLLM(failures=1)
    parsed = asyncio.run(
        ainvoke_structured(llm, BatchReviewOutput, [{"role": "user", "content": "review"}])
    )

    assert parsed.batch_id == "batch-1"
    assert llm.kwargs == {"schema": BatchReviewOutput, "include_raw": True}
    assert len(llm.runnable.calls) == 2
    resent = json.dumps(llm.runnable.calls[1])
    assert "String should have at least 1 character" in resent
    assert "batch_id" in resent

    failing = FakeLLM(failures=2)
    with pytest.raises(AppError) as caught:
        asyncio.run(
            ainvoke_structured(
                failing,
                BatchReviewOutput,
                [{"role": "user", "content": "review"}],
            )
        )
    assert failing.runnable.calls.__len__() == 2
    assert caught.value.code == "ai_structured_output_invalid"
    assert "String should have at least 1 character" in caught.value.message
