from app.services.evidence_redaction_service import (
    REDACTION_MARKER,
    redact_json_like,
    redact_text,
)


def test_redact_text_masks_github_tokens_private_keys_and_assignments():
    text = (
        "clone https://x-access-token:ghs_abcdefghijklmnopqrstuvwxyz123456@github.com/o/r\n"
        "pat github_pat_abcdefghijklmnopqrstuv_wxyz1234567890\n"
        "oauth gho_abcdefghijklmnopqrstuvwxyz123456\n"
        "openai sk-proj-abcdefghijklmnopqrstuvwxyz1234567890\n"
        "+ SECRET_KEY=super-secret-value\n"
        "+ PASSWORD: hunter2\n"
        "-----BEGIN OPENSSH PRIVATE KEY-----\n"
        "private-material\n"
        "-----END OPENSSH PRIVATE KEY-----\n"
        "tests passed: 12 ok"
    )

    redacted = redact_text(text)

    assert "ghs_abcdefghijklmnopqrstuvwxyz123456" not in redacted
    assert "github_pat_abcdefghijklmnopqrstuv" not in redacted
    assert "gho_abcdefghijklmnopqrstuvwxyz123456" not in redacted
    assert "sk-proj-abcdefghijklmnopqrstuvwxyz" not in redacted
    assert "super-secret-value" not in redacted
    assert "hunter2" not in redacted
    assert "private-material" not in redacted
    assert "tests passed: 12 ok" in redacted
    assert REDACTION_MARKER in redacted


def test_redact_json_like_redacts_nested_patch_without_mutating_input():
    evidence = {
        "filename": "src/app.py",
        "patch": "+OPENAI_API_KEY=sk-proj-abcdefghijklmnopqrstuvwxyz1234567890",
        "findings": [
            {
                "title": "Hardcoded token",
                "description": "saw github_pat_abcdefghijklmnopqrstuv_wxyz1234567890",
                "line_number": 7,
                "blocking": True,
            }
        ],
    }

    redacted = redact_json_like(evidence)

    assert redacted["filename"] == "src/app.py"
    assert redacted["findings"][0]["line_number"] == 7
    assert redacted["findings"][0]["blocking"] is True
    assert "sk-proj-abcdefghijklmnopqrstuvwxyz" not in redacted["patch"]
    assert (
        "github_pat_abcdefghijklmnopqrstuv"
        not in redacted["findings"][0]["description"]
    )
    assert REDACTION_MARKER in redacted["patch"]
    assert evidence["patch"].endswith("abcdefghijklmnopqrstuvwxyz1234567890")
