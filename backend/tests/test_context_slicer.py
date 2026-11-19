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


def test_diff_parser_covers_headers_metadata_and_merged_hunks():
    preamble = "\n".join(
        [
            "not a diff header",
            "@@ -1 +1 @@",
            "-old",
            "+new",
            "\\ No newline at end of file",
            'diff --git "a/my file.py" "b/my file.py"',
            '--- "a/my file.py"',
            '+++ "b/my file.py"',
            "@@ -0,0 +1,1 @@",
            "+value = 1",
            "diff --git a/old.py b/old.py",
            "deleted file mode 100644",
            "--- a/old.py",
            "+++ /dev/null",
            "@@ -1 +0,0 @@",
            "-removed",
            "diff --git a/src/app.py b/src/app.py",
            "--- a/src/app.py",
            "+++ file.py",
            "@@ -0,0 +1,1 @@",
            "+first = 1",
            "diff --git a/src/app.py b/src/app.py",
            "index 111..222 100644",
            "new file mode 100644",
            "similarity index 90%",
            "rename from src/old.py",
            "copy from src/other.py",
            "old mode 100644",
            "--- a/src/app.py",
            "+++ b/src/app.py",
            "@@ -0,0 +1,1 @@",
            "+second = 2",
            "diff --git noslash",
            "GIT binary patch",
            "",
        ]
    )

    lines = valid_lines_for_diff(preamble)

    assert lines["unknown"] == [1]
    assert lines["my file.py"] == [1]
    assert lines["old.py"] == []
    assert lines["src/app.py"] == [1]
    assert "noslash" not in lines or lines.get("unknown")


def test_slice_skips_unusable_files_and_uses_collapsed_secrets():
    private_key = "\n".join(
        [
            "diff --git a/src/keys.py b/src/keys.py",
            "--- a/src/keys.py",
            "+++ b/src/keys.py",
            "@@ -1,3 +1,3 @@",
            " -----BEGIN PRIVATE KEY-----",
            "+abcdef",
            " -----END PRIVATE KEY-----",
        ]
    )
    collapsed = slice_review_batches(private_key, max_batch_chars=8000, max_batches=2)
    assert "BEGIN PRIVATE KEY" not in collapsed.batches[0]["diff_text"]
    assert REDACTION_MARKER in collapsed.batches[0]["diff_text"]

    tiny = slice_review_batches(_added("src/app.py", ["value = 1"]), max_batch_chars=1, max_batches=2)
    assert tiny.batches == []
    assert tiny.review_truncated is True
    assert tiny.skipped_files == ["src/app.py"]

    nothing = slice_review_batches("", max_batch_chars=0, max_batches=0)
    assert nothing.batches_sent == 0
    assert nothing.review_truncated is False


def test_digests_cover_budget_alerts_and_non_dict_inputs():
    short = build_coverage_digest(
        mode="hybrid",
        deterministic_status=None,
        max_chars=None,
    )
    assert short.pillar_max_chars == 8000
    assert "blocking_reasons:" in short.digest["evidence_text"]
    assert short.review_truncated is False

    clipped = build_coverage_digest(
        mode="hybrid",
        deterministic_status="fail",
        uncovered_lines_by_file={".\\src\\app.py": [1]},
        diff_text=_added("src/app.py", ["gap = True", "API_KEY=x"]),
        max_chars=5,
    )
    assert clipped.review_truncated is True
    assert len(clipped.digest["evidence_text"]) <= 5

    empty_budget = build_security_digest(
        mode="hybrid",
        deterministic_status="pass",
        max_chars=0,
    )
    assert empty_budget.digest["evidence_text"] == ""
    assert empty_budget.review_truncated is True

    security = build_security_digest(
        mode="hybrid",
        deterministic_status="pass",
        diff_text="\n".join(
            [
                _added("package-lock.json", ["password = 'skip-me'"]),
                _added("src/auth.py", ["password = 'keep'"]),
                _added("src/net.py", ["requests.get('https://example.com')"]),
            ]
        ),
        alerts=[
            None,
            {"path": "./src/auth.py", "scanner": "", "rule_id": "hardcoded"},
            {"file_path": "   ", "title": ""},
        ],
        max_chars=220,
    )
    assert "package-lock.json" not in security.digest["evidence_text"]
    assert security.review_truncated is True
    assert "src/net.py" in security.skipped_files or "src/auth.py" in security.skipped_files

    debt = build_debt_digest(
        mode="ai_only",
        deterministic_status="pass",
        findings=[None, {"filename": "src/plain.py", "title": "Note"}],
        diff_text=_added("src/plain.py", ["TODO: later"]),
        snapshot=None,
        max_chars=8000,
    )
    assert "src/plain.py" in debt.digest["evidence_text"]
    assert "Note" in debt.digest["evidence_text"]


def test_ainvoke_structured_accepts_raw_shapes_and_rejects_bad_attempts():
    class Scripted:
        def __init__(self, results):
            self.results = results
            self.calls = []

        async def ainvoke(self, messages):
            self.calls.append(messages)
            return self.results[len(self.calls) - 1]

    class LLM:
        def __init__(self, results):
            self.runnable = Scripted(results)

        def with_structured_output(self, schema, include_raw=False):
            assert include_raw is True
            return self.runnable

    direct = asyncio.run(
        ainvoke_structured(
            LLM([BatchReviewOutput(batch_id="direct", summary="ok")]),
            BatchReviewOutput,
            [],
        )
    )
    assert direct.batch_id == "direct"

    from_dict = asyncio.run(
        ainvoke_structured(
            LLM(
                [
                    {
                        "parsed": {"batch_id": "from-dict", "summary": "ok"},
                        "parsing_error": None,
                        "raw": {"content": "ok"},
                    }
                ]
            ),
            BatchReviewOutput,
            [],
        )
    )
    assert from_dict.batch_id == "from-dict"

    class Raw:
        content = 5

    recovered = asyncio.run(
        ainvoke_structured(
            LLM(
                [
                    {"parsed": None, "parsing_error": RuntimeError("boom"), "raw": "raw-text"},
                    {"parsed": None, "parsing_error": None, "raw": None},
                    {"parsed": None, "parsing_error": ValueError("again"), "raw": Raw()},
                    BatchReviewOutput(batch_id="recovered", summary="ok"),
                ]
            ),
            BatchReviewOutput,
            [{"role": "user", "content": "review"}],
            max_attempts=4,
        )
    )
    assert recovered.batch_id == "recovered"

    runner = LLM(
        [
            {"parsed": None, "parsing_error": RuntimeError("boom"), "raw": "raw-text"},
            {"parsed": None, "parsing_error": None, "raw": None},
            {"parsed": None, "parsing_error": ValueError("again"), "raw": Raw()},
            BatchReviewOutput(batch_id="recovered", summary="ok"),
        ]
    )
    parsed = asyncio.run(
        ainvoke_structured(runner, BatchReviewOutput, [{"role": "user", "content": "review"}], max_attempts=4)
    )
    blob = json.dumps(runner.runnable.calls, default=str)
    assert parsed.batch_id == "recovered"
    assert "boom" in blob
    assert "Structured output was empty." in blob
    assert "again" in blob

    with pytest.raises(AppError) as caught:
        asyncio.run(ainvoke_structured(LLM([]), BatchReviewOutput, [], max_attempts=0))
    assert caught.value.status_code == 400

    plain = asyncio.run(
        ainvoke_structured(
            LLM([{"batch_id": "plain", "summary": "ok"}]),
            BatchReviewOutput,
            [],
        )
    )
    assert plain.batch_id == "plain"

    class Flaky:
        def __init__(self):
            self.calls = 0

        async def ainvoke(self, messages):
            self.calls += 1
            if self.calls == 1:
                return "not-json"
            return BatchReviewOutput(batch_id="after-text", summary="ok")

    class FlakyLLM:
        def __init__(self):
            self.runnable = Flaky()

        def with_structured_output(self, schema, include_raw=False):
            return self.runnable

    after_text = asyncio.run(
        ainvoke_structured(FlakyLLM(), BatchReviewOutput, [{"role": "user", "content": "review"}])
    )
    assert after_text.batch_id == "after-text"


def test_slice_budget_edges_and_duplicate_lines():
    duplicate = "\n".join(
        [
            "diff --git a/src/app.py b/src/app.py",
            "--- a/src/app.py",
            "+++ b/src/app.py",
            "@@ -0,0 +1,1 @@",
            "+first",
            "@@ -0,0 +1,1 @@",
            "+second",
            "diff --git a//dev/null b//dev/null",
            "--- a//dev/null",
            "+++ b//dev/null",
            "@@ -1 +0,0 @@",
            "-gone",
        ]
    )
    assert valid_lines_for_diff(duplicate)["src/app.py"] == [1]
    omitted = slice_review_batches(duplicate, max_batch_chars=8000, max_batches=2)
    assert omitted.skipped_files == ["/dev/null"]
    assert omitted.batches[0]["file_paths"] == ["src/app.py"]

    blocked = slice_review_batches(_added("src/app.py", ["value = 1"]), max_batch_chars=0, max_batches=1)
    assert blocked.batches == []
    assert blocked.review_truncated is True

    growing = _added("src/app.py", ["API_KEY=x"])
    raw = growing if growing.endswith("\n") else growing + "\n"
    fitted = slice_review_batches(raw, max_batch_chars=len(raw.strip()), max_batches=1)
    assert REDACTION_MARKER in fitted.batches[0]["diff_text"] or fitted.review_truncated is True

    skipped = build_security_digest(
        mode="hybrid",
        deterministic_status="pass",
        diff_text="\n".join(
            [
                "diff --git a/src/auth.py b/src/auth.py",
                "--- a/src/auth.py",
                "+++ b/src/auth.py",
                "@@ -1 +1 @@",
                "-old",
                "+password = 'one'",
                "@@ -3 +3 @@",
                "-old",
                "+password = 'two'",
            ]
        ),
        max_chars=40,
    )
    assert skipped.review_truncated is True
    assert skipped.skipped_files.count("src/auth.py") == 1
