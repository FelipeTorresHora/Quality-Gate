from __future__ import annotations

import re
from typing import Any

REDACTION_MARKER = "***REDACTED***"

_SECRET_PATTERNS = [
    re.compile(r"x-access-token:[^@\s]+@"),
    re.compile(r"\bghs_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bgho_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bsk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{20,}\b"),
    re.compile(
        r"-----BEGIN[ A-Z]*PRIVATE KEY-----.*?-----END[ A-Z]*PRIVATE KEY-----",
        re.S,
    ),
    re.compile(
        r"(?im)^(\s*[+-]?\s*[A-Z0-9_]*"
        r"(?:SECRET|TOKEN|PASSWORD|API_KEY|PRIVATE_KEY)"
        r"[A-Z0-9_]*\s*[:=]\s*)([^\s#]+)"
    ),
]


def redact_text(text: str) -> str:
    redacted = text
    for pattern in _SECRET_PATTERNS:
        if pattern.groups >= 2:
            redacted = pattern.sub(rf"\1{REDACTION_MARKER}", redacted)
        else:
            redacted = pattern.sub(REDACTION_MARKER, redacted)
    return redacted


def redact_json_like(value: Any) -> Any:
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, list):
        return [redact_json_like(item) for item in value]
    if isinstance(value, dict):
        return {key: redact_json_like(item) for key, item in value.items()}
    return value
