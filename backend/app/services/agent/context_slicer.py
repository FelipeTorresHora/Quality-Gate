from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Literal

from app.core.config import get_settings
from app.services.agent.state import BatchInput, PillarDigest
from app.services.evidence_redaction_service import redact_json_like

EvaluationMode = Literal["hybrid", "deterministic", "ai_only"]

_HUNK_HEADER = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")
_LOCKFILE_NAMES = {
    "bun.lock",
    "bun.lockb",
    "cargo.lock",
    "composer.lock",
    "gemfile.lock",
    "go.sum",
    "gradle.lockfile",
    "mix.lock",
    "npm-shrinkwrap.json",
    "package-lock.json",
    "packages.lock.json",
    "pipfile.lock",
    "pnpm-lock.yaml",
    "pnpm-lock.yml",
    "podfile.lock",
    "poetry.lock",
    "pubspec.lock",
    "shrinkwrap.json",
    "shrinkwrap.yaml",
    "uv.lock",
    "yarn.lock",
}
_BINARY_SUFFIXES = (
    ".bin",
    ".class",
    ".dll",
    ".dylib",
    ".eot",
    ".exe",
    ".gif",
    ".gz",
    ".ico",
    ".jar",
    ".jpeg",
    ".jpg",
    ".mp3",
    ".mp4",
    ".pdf",
    ".png",
    ".so",
    ".svg",
    ".tar",
    ".tgz",
    ".ttf",
    ".wasm",
    ".wav",
    ".webp",
    ".woff",
    ".woff2",
    ".zip",
)
_SENSITIVE = re.compile(
    r"("
    r"\b(auth(?:entication|orization)?|password|passwd|token|session|jwt|oauth|login|credential)\b"
    r"|\b(?:select|insert|update|delete)\b.{0,80}\b(?:from|into|set|table)\b"
    r"|\b(?:sql|sqli)\b|cursor\.execute|sqlalchemy|\.execute\("
    r"|\bexec\(|\beval\(|subprocess|os\.system|child_process|shell\s*=\s*True"
    r"|\b(crypto|cipher|hashlib|bcrypt|encrypt|decrypt|hmac)\b"
    r"|https?://|\brequests\.|\bfetch\(|\baxios\b|http\.Client|XMLHttpRequest"
    r"|\bopen\(|\breadFile\b|\bwriteFile\b|os\.remove|\bfs\.|\bioutil\b"
    r"|pickle\.|yaml\.load|\bunmarshal\b|ObjectInputStream|\bunserialize\b|jsonpickle|\bdeserializ"
    r")",
    re.IGNORECASE,
)
_TRUNCATION_MARKER = "\n[truncated]"


@dataclass
class Hunk:
    header: str
    body: list[str] = field(default_factory=list)
    valid_lines: list[int] = field(default_factory=list)


@dataclass
class ParsedFile:
    path: str
    raw_lines: list[str] = field(default_factory=list)
    hunks: list[Hunk] = field(default_factory=list)
    is_binary: bool = False

    def valid_lines(self) -> list[int]:
        return _dedupe_ints(line for hunk in self.hunks for line in hunk.valid_lines)


@dataclass(frozen=True)
class ReviewSlice:
    """Planner output the code-review graph copies onto ReviewGraphState.

    `batches` are the batches to invoke. `batches_total` counts every batch
    the packer built. `skipped_files` is deduped. Noise files are listed there
    and do not set `review_truncated`; budget clips and dropped source files do.
    """

    batches: list[BatchInput]
    skipped_files: list[str]
    review_truncated: bool
    batches_total: int
    batches_sent: int
    valid_lines_by_file: dict[str, list[int]]
    batch_max_chars: int
    max_batches: int


@dataclass(frozen=True)
class PillarDigestResult:
    """One capped pillar input. `digest` is the PillarDigest state value."""

    digest: PillarDigest
    review_truncated: bool
    skipped_files: list[str]
    pillar_max_chars: int


def valid_lines_for_diff(diff_text: str) -> dict[str, list[int]]:
    """RIGHT-side line numbers that exist in each file's patch.

    Deleted lines are excluded. The code-review graph may cite only numbers
    from this set (or from the subset stored on each BatchInput).
    """

    result: dict[str, list[int]] = {}
    for parsed in parse_unified_diff(diff_text):
        result[parsed.path] = parsed.valid_lines()
    return result


def parse_unified_diff(diff_text: str) -> list[ParsedFile]:
    """Parse a unified diff into per-file hunks with right-side line numbers."""

    files: list[ParsedFile] = []
    current: ParsedFile | None = None
    hunk: Hunk | None = None
    new_line = 0

    def start(path: str) -> None:
        nonlocal current, hunk
        current = ParsedFile(path=path)
        files.append(current)
        hunk = None

    for line in (diff_text or "").splitlines():
        if line.startswith("diff --git "):
            old, new = _git_paths(line)
            start(new or old or "unknown")
            current.raw_lines.append(line)
            continue
        if current is None and (
            line.startswith("--- ") or line.startswith("+++ ") or line.startswith("@@")
        ):
            start("unknown")
        if current is None:
            continue
        if line.startswith("Binary files ") or line.startswith("GIT binary patch"):
            current.is_binary = True
            current.raw_lines.append(line)
            hunk = None
            continue
        if hunk is None and line.startswith("+++ "):
            updated = _header_path(line)
            if updated and updated != "/dev/null":
                current.path = updated
            current.raw_lines.append(line)
            continue
        if hunk is None and _is_diff_metadata(line):
            current.raw_lines.append(line)
            continue
        header = _HUNK_HEADER.match(line)
        if header:
            new_line = int(header.group(3))
            hunk = Hunk(header=line)
            current.hunks.append(hunk)
            current.raw_lines.append(line)
            continue
        current.raw_lines.append(line)
        if hunk is None or line.startswith("\\"):
            if hunk is not None:
                hunk.body.append(line)
            continue
        if line.startswith("+"):
            hunk.valid_lines.append(new_line)
            hunk.body.append(line)
            new_line += 1
            continue
        if line.startswith("-"):
            hunk.body.append(line)
            continue
        if line.startswith(" "):
            hunk.valid_lines.append(new_line)
            hunk.body.append(line)
            new_line += 1
            continue
        hunk.body.append(line)
    return _merge_parsed(files)


def slice_review_batches(
    diff_text: str,
    *,
    security_alerts: list[dict[str, Any]] | None = None,
    uncovered_lines_by_file: dict[str, list[int]] | None = None,
    max_batch_chars: int | None = None,
    max_batches: int | None = None,
) -> ReviewSlice:
    """Pack a redacted diff into risk-ordered batches.

    Order is files with security alerts, then files with uncovered lines, then
    the largest remaining source hunks. `max_batch_chars` and `max_batches`
    default to Settings.ai_batch_max_chars (8000) and Settings.ai_max_batches (12).
    """

    settings = get_settings()
    batch_chars = settings.ai_batch_max_chars if max_batch_chars is None else max_batch_chars
    batch_limit = settings.ai_max_batches if max_batches is None else max_batches
    alert_paths = _alert_paths(security_alerts)
    uncovered = uncovered_lines_by_file or {}
    prepared: list[_Prepared] = []
    omitted: list[str] = []
    review_truncated = False

    for parsed in parse_unified_diff(diff_text):
        if _is_omitted_path(parsed.path, parsed.is_binary):
            omitted.append(parsed.path)
            continue
        fitted = _fit_file(parsed, batch_chars)
        if fitted is None:
            omitted.append(parsed.path)
            review_truncated = True
            continue
        prepared.append(fitted)
        if fitted.clipped:
            review_truncated = True

    prepared.sort(key=lambda item: _risk_key(item, alert_paths, uncovered))
    packed = _pack(prepared, batch_chars)
    batches_total = len(packed)
    sent = packed[: max(batch_limit, 0)]
    if batch_limit < batches_total:
        review_truncated = True
        for group in packed[max(batch_limit, 0) :]:
            omitted.extend(item.path for item in group)

    batches: list[BatchInput] = []
    valid_lines: dict[str, list[int]] = {}
    for index, group in enumerate(sent, start=1):
        redacted_parts = redact_json_like([item.diff_text for item in group])
        parts = redacted_parts if isinstance(redacted_parts, list) else [item.diff_text for item in group]
        diff_parts = [part if isinstance(part, str) else "" for part in parts]
        batch_lines: dict[str, list[int]] = {}
        for item, text in zip(group, diff_parts, strict=True):
            lines = item.valid_lines
            if text.count("\n") != item.diff_text.count("\n"):
                lines = _valid_from_text(text)
            batch_lines[item.path] = lines
            valid_lines[item.path] = _dedupe_ints([*valid_lines.get(item.path, []), *lines])
        batches.append(
            {
                "batch_id": f"batch-{index}",
                "file_paths": [item.path for item in group],
                "diff_text": "\n".join(diff_parts),
                "valid_lines_by_file": batch_lines,
            }
        )

    return ReviewSlice(
        batches=batches,
        skipped_files=_dedupe_paths(omitted),
        review_truncated=review_truncated,
        batches_total=batches_total,
        batches_sent=len(batches),
        valid_lines_by_file=valid_lines,
        batch_max_chars=batch_chars,
        max_batches=batch_limit,
    )


def build_coverage_digest(
    *,
    mode: EvaluationMode,
    deterministic_status: str | None,
    uncovered_lines_by_file: dict[str, list[int]] | None = None,
    diff_text: str = "",
    pr_coverage: float | None = None,
    changed_files_coverage: float | None = None,
    blocking_reasons: list[str] | None = None,
    max_chars: int | None = None,
) -> PillarDigestResult:
    """Coverage evidence for changed files, capped at Settings.ai_pillar_max_chars."""

    uncovered = uncovered_lines_by_file or {}
    sections = [
        (
            "",
            _block(
                [
                    f"deterministic_status: {deterministic_status}",
                    f"pr_coverage: {pr_coverage}",
                    f"changed_files_coverage: {changed_files_coverage}",
                    *_bullet("blocking_reasons", blocking_reasons or []),
                    *_bullet(
                        "uncovered_lines",
                        [
                            f"{path}: {', '.join(str(number) for number in lines)}"
                            for path, lines in uncovered.items()
                            if lines
                        ],
                    ),
                ]
            ),
        )
    ]
    sections.extend(_selected_hunks(diff_text, lambda parsed, hunk: _hunk_hits_uncovered(parsed.path, hunk, uncovered)))
    return _finish_digest("coverage", mode, deterministic_status, sections, max_chars)


def build_security_digest(
    *,
    mode: EvaluationMode,
    deterministic_status: str | None,
    diff_text: str = "",
    alerts: list[dict[str, Any]] | None = None,
    max_chars: int | None = None,
) -> PillarDigestResult:
    """Sensitive hunks plus scanner alerts, capped at Settings.ai_pillar_max_chars.

    A hunk is included when it matches auth, SQL, exec, crypto, HTTP, IO, or
    deserialization, or when its file has a scanner alert.
    """

    alert_rows = [_format_alert(alert) for alert in alerts or [] if isinstance(alert, dict)]
    alert_paths = _alert_paths(alerts)
    sections = [
        (
            "",
            _block(
                [
                    f"deterministic_status: {deterministic_status}",
                    *_bullet("alerts", [row for row in alert_rows if row]),
                ]
            ),
        )
    ]

    def selected(parsed: ParsedFile, hunk: Hunk) -> bool:
        path = _normalize_repo_path(parsed.path)
        if path in alert_paths:
            return True
        return _SENSITIVE.search(hunk.header + "\n" + "\n".join(hunk.body)) is not None

    sections.extend(_selected_hunks(diff_text, selected, preferred_paths=alert_paths))
    return _finish_digest("security", mode, deterministic_status, sections, max_chars)


def build_debt_digest(
    *,
    mode: EvaluationMode,
    deterministic_status: str | None,
    findings: list[dict[str, Any]] | None = None,
    diff_text: str = "",
    snapshot: dict[str, Any] | None = None,
    max_chars: int | None = None,
) -> PillarDigestResult:
    """Technical-debt findings and their hunks, capped at Settings.ai_pillar_max_chars."""

    finding_rows: list[str] = []
    finding_paths: set[str] = set()
    for finding in findings or []:
        if not isinstance(finding, dict):
            continue
        path = finding.get("file_path") or finding.get("filename")
        if isinstance(path, str) and path.strip():
            finding_paths.add(_normalize_repo_path(path))
        finding_rows.append(_format_finding(finding))
    snapshot = snapshot or {}
    sections = [
        (
            "",
            _block(
                [
                    f"deterministic_status: {deterministic_status}",
                    f"new_todo_count: {snapshot.get('new_todo_count')}",
                    f"function_length_count: {snapshot.get('function_length_count')}",
                    f"complexity_count: {snapshot.get('complexity_count')}",
                    *_bullet("blocking_reasons", snapshot.get("blocking_reasons") or []),
                    *_bullet("findings", finding_rows),
                ]
            ),
        )
    ]
    sections.extend(
        _selected_hunks(
            diff_text,
            lambda parsed, _hunk: _normalize_repo_path(parsed.path) in finding_paths,
            preferred_paths=finding_paths,
        )
    )
    return _finish_digest("technical_debt", mode, deterministic_status, sections, max_chars)


@dataclass
class _Prepared:
    path: str
    diff_text: str
    valid_lines: list[int]
    clipped: bool
    rank_size: int


def _fit_file(parsed: ParsedFile, max_chars: int) -> _Prepared | None:
    raw_lines = parsed.raw_lines
    raw = "\n".join(raw_lines)
    if not raw or max_chars < 1:
        return None
    redacted = _as_text(redact_json_like(raw))
    valid = parsed.valid_lines()
    if raw.count("\n") != redacted.count("\n"):
        valid = _valid_from_text(redacted)
    if len(redacted) <= max_chars:
        return _Prepared(parsed.path, redacted, valid, False, len(raw))

    kept: list[str] = []
    size = 0
    for line in raw_lines:
        extra = len(line) + (1 if kept else 0)
        if size + extra > max_chars:
            break
        kept.append(line)
        size += extra
    while kept:
        original = "\n".join(kept)
        redacted = _as_text(redact_json_like(original))
        if redacted and len(redacted) <= max_chars:
            source = original if original.count("\n") == redacted.count("\n") else redacted
            return _Prepared(parsed.path, redacted, _valid_from_text(source), True, len(raw))
        kept.pop()
    return None


def _pack(prepared: list[_Prepared], max_chars: int) -> list[list[_Prepared]]:
    groups: list[list[_Prepared]] = []
    current: list[_Prepared] = []
    current_len = 0
    for item in prepared:
        extra = len(item.diff_text) if not current else len(item.diff_text) + 1
        if current and current_len + extra > max_chars:
            groups.append(current)
            current = []
            current_len = 0
            extra = len(item.diff_text)
        current.append(item)
        current_len += extra
    if current:
        groups.append(current)
    return groups


def _risk_key(
    item: _Prepared,
    alert_paths: set[str],
    uncovered: dict[str, list[int]],
) -> tuple[int, int, str]:
    path = _normalize_repo_path(item.path)
    if path in alert_paths:
        tier = 0
    elif _has_uncovered(path, uncovered):
        tier = 1
    else:
        tier = 2
    return (tier, -item.rank_size, path)


def _selected_hunks(
    diff_text: str,
    predicate,
    preferred_paths: set[str] | None = None,
) -> list[tuple[str, str]]:
    preferred_paths = preferred_paths or set()
    chosen: list[tuple[int, int, str, str]] = []
    for parsed in parse_unified_diff(diff_text):
        if _is_omitted_path(parsed.path, parsed.is_binary):
            continue
        path = _normalize_repo_path(parsed.path)
        for hunk in parsed.hunks:
            if not predicate(parsed, hunk):
                continue
            text = "\n".join([f"diff --git a/{parsed.path} b/{parsed.path}", hunk.header, *hunk.body])
            tier = 0 if path in preferred_paths else 1
            chosen.append((tier, -len(text), parsed.path, text))
    chosen.sort(key=lambda item: (item[0], item[1], item[2]))
    return [(path, text) for _tier, _size, path, text in chosen]


def _hunk_hits_uncovered(path: str, hunk: Hunk, uncovered: dict[str, list[int]]) -> bool:
    wanted = set(_lookup_lines(path, uncovered))
    return bool(wanted.intersection(hunk.valid_lines))


def _finish_digest(
    pillar: Literal["coverage", "security", "technical_debt"],
    mode: EvaluationMode,
    deterministic_status: str | None,
    sections: list[tuple[str, str]],
    max_chars: int | None,
) -> PillarDigestResult:
    limit = get_settings().ai_pillar_max_chars if max_chars is None else max_chars
    redacted_sections: list[tuple[str, str]] = []
    for path, text in sections:
        redacted = redact_json_like(text)
        redacted_sections.append((path, redacted if isinstance(redacted, str) else ""))
    evidence, truncated, skipped = _bound_sections(redacted_sections, limit)
    digest: PillarDigest = {
        "pillar": pillar,
        "mode": mode,
        "deterministic_status": deterministic_status,
        "evidence_text": evidence,
    }
    return PillarDigestResult(
        digest=digest,
        review_truncated=truncated,
        skipped_files=skipped,
        pillar_max_chars=limit,
    )


def _bound_sections(
    sections: list[tuple[str, str]],
    max_chars: int,
) -> tuple[str, bool, list[str]]:
    kept: list[str] = []
    used = 0
    skipped: list[str] = []
    truncated = False
    skipping = False
    for path, text in sections:
        if not text:
            continue
        if skipping:
            truncated = True
            if path:
                skipped.append(path)
            continue
        extra = len(text) if not kept else len(text) + 1
        if not kept and len(text) > max_chars:
            kept.append(_cap(text, max_chars))
            truncated = True
            skipping = True
            continue
        if kept and used + extra > max_chars:
            truncated = True
            skipping = True
            if path:
                skipped.append(path)
            continue
        kept.append(text)
        used += extra
    return "\n".join(kept), truncated, _dedupe_paths(skipped)


def _cap(text: str, max_chars: int) -> str:
    if max_chars < 1:
        return ""
    if len(text) <= max_chars:
        return text
    if max_chars <= len(_TRUNCATION_MARKER):
        return text[:max_chars]
    return text[: max_chars - len(_TRUNCATION_MARKER)] + _TRUNCATION_MARKER


def _block(lines: list[str]) -> str:
    return "\n".join(line for line in lines if line)


def _bullet(title: str, rows: list[Any]) -> list[str]:
    rendered = [str(row) for row in rows if row is not None and str(row) != ""]
    if not rendered:
        return [f"{title}:"]
    return [f"{title}:", *[f"- {row}" for row in rendered]]


def _format_alert(alert: dict[str, Any]) -> str:
    scanner = alert.get("scanner") or "scanner"
    path = alert.get("file_path") or alert.get("filename") or alert.get("path") or ""
    line = alert.get("line_number")
    location = f"{path}:{line}" if path and line else str(path or "")
    title = alert.get("title") or alert.get("rule_id") or ""
    severity = alert.get("severity") or ""
    return " ".join(part for part in (str(scanner), location, str(severity), str(title)) if part).strip()


def _format_finding(finding: dict[str, Any]) -> str:
    path = finding.get("file_path") or finding.get("filename") or ""
    line = finding.get("line_number")
    location = f"{path}:{line}" if path and line else str(path or "")
    title = finding.get("title") or ""
    description = finding.get("description") or ""
    severity = finding.get("severity") or ""
    return " ".join(
        part for part in (str(severity), location, str(title), str(description)) if part
    ).strip()


def _valid_from_text(text: str) -> list[int]:
    return _dedupe_ints(
        line for parsed in parse_unified_diff(text) for line in parsed.valid_lines()
    )


def _merge_parsed(files: list[ParsedFile]) -> list[ParsedFile]:
    order: list[str] = []
    grouped: dict[str, ParsedFile] = {}
    for parsed in files:
        path = _normalize_repo_path(parsed.path)
        parsed.path = path
        current = grouped.get(path)
        if current is None:
            grouped[path] = parsed
            order.append(path)
            continue
        current.raw_lines.extend(parsed.raw_lines)
        current.hunks.extend(parsed.hunks)
        current.is_binary = current.is_binary or parsed.is_binary
    return [grouped[path] for path in order]


def _git_paths(line: str) -> tuple[str, str]:
    body = line[len("diff --git ") :]
    if body.startswith('"'):
        match = re.match(r'^"((?:\\.|[^"])*)"\s+"((?:\\.|[^"])*)"$', body)
        if match:
            return _strip_ab(_unescape(match.group(1))), _strip_ab(_unescape(match.group(2)))
    marker = " b/"
    index = body.rfind(marker)
    if body.startswith("a/") and index > 0:
        return body[2:index], body[index + len(marker) :]
    return "", ""


def _header_path(line: str) -> str:
    raw = line[4:].split("\t", 1)[0].strip()
    if len(raw) >= 2 and raw[0] == '"' and raw[-1] == '"':
        raw = _unescape(raw[1:-1])
    if raw == "/dev/null":
        return raw
    return _strip_ab(raw)


def _strip_ab(path: str) -> str:
    if path.startswith("a/") or path.startswith("b/"):
        return path[2:]
    return path


def _unescape(value: str) -> str:
    return value.replace("\\", "")


def _is_diff_metadata(line: str) -> bool:
    return line.startswith(
        (
            "--- ",
            "index ",
            "new file ",
            "deleted file ",
            "similarity ",
            "rename ",
            "old mode ",
            "new mode ",
            "copy ",
            "dissimilarity ",
        )
    )


def _is_omitted_path(path: str, is_binary: bool) -> bool:
    normalized = _normalize_repo_path(path)
    if normalized in {"", "/dev/null"}:
        return True
    parts = [part for part in normalized.split("/") if part]
    name = parts[-1].lower() if parts else ""
    lowered = {part.lower() for part in parts}
    if name in _LOCKFILE_NAMES:
        return True
    if "node_modules" in lowered or "dist" in lowered:
        return True
    if name.endswith(".min.js") or name.endswith(".map") or name.endswith(".svg") or name.endswith(".png"):
        return True
    if is_binary or any(name.endswith(suffix) for suffix in _BINARY_SUFFIXES):
        return True
    return False


def _alert_paths(alerts: list[dict[str, Any]] | None) -> set[str]:
    paths: set[str] = set()
    for alert in alerts or []:
        if not isinstance(alert, dict):
            continue
        for key in ("file_path", "filename", "path"):
            value = alert.get(key)
            if isinstance(value, str) and value.strip():
                paths.add(_normalize_repo_path(value))
                break
    return paths


def _has_uncovered(path: str, uncovered: dict[str, list[int]]) -> bool:
    return bool(_lookup_lines(path, uncovered))


def _lookup_lines(path: str, uncovered: dict[str, list[int]]) -> list[int]:
    normalized = _normalize_repo_path(path)
    for key, lines in uncovered.items():
        if _normalize_repo_path(str(key)) == normalized:
            return list(lines or [])
    return []


def _normalize_repo_path(path: str) -> str:
    normalized = path.replace("\\", "/").strip()
    if normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def _as_text(value: Any) -> str:
    return value if isinstance(value, str) else ""


def _dedupe_paths(paths: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for path in paths:
        if not path or path in seen:
            continue
        seen.add(path)
        result.append(path)
    return result


def _dedupe_ints(values) -> list[int]:
    seen: set[int] = set()
    result: list[int] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
