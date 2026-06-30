from app.services.runner_service import CommandResult, _safe_env, redact_secrets


def test_safe_env_does_not_leak_app_secrets(monkeypatch):
    monkeypatch.setenv("SESSION_SECRET", "super-secret")
    monkeypatch.setenv("TOKEN_ENCRYPTION_KEY", "enc-key")
    monkeypatch.setenv("GITHUB_APP_PRIVATE_KEY", "pk")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-x")
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@h/db")
    env = _safe_env()
    assert "SESSION_SECRET" not in env
    assert "TOKEN_ENCRYPTION_KEY" not in env
    assert "GITHUB_APP_PRIVATE_KEY" not in env
    assert "OPENAI_API_KEY" not in env
    assert "DATABASE_URL" not in env
    assert "PATH" in env


def test_safe_env_keeps_toolchain_variables(monkeypatch):
    monkeypatch.setenv("GOPATH", "/go")
    monkeypatch.setenv("NODE_ENV", "production")
    env = _safe_env()
    assert env["GOPATH"] == "/go"
    assert env["NODE_ENV"] == "production"


def test_safe_env_defaults_path_when_absent(monkeypatch):
    monkeypatch.delenv("PATH", raising=False)
    env = _safe_env()
    assert env["PATH"]


def test_redact_secrets_masks_tokens_and_clone_credentials():
    text = (
        "cloning https://x-access-token:ghs_abcdefghijklmnopqrstuvwxyz@github.com/o/r\n"
        "token ghs_abcdefghijklmnopqrstuvwxyz12345\n"
        "pat github_pat_abcdefghijklmnopqrstuv_wxyz\n"
        "oauth gho_abcdefghijklmnopqrstuvwxyz\n"
    )
    redacted = redact_secrets(text)
    assert "ghs_abcdefghijklmnopqrstuvwxyz" not in redacted
    assert "github_pat_abcdefghijklmnopqrstuv" not in redacted
    assert "gho_abcdefghijklmnopqrstuvwxyz" not in redacted
    assert "x-access-token:ghs_" not in redacted
    assert "***REDACTED***" in redacted


def test_redact_secrets_masks_private_key_block():
    text = (
        "-----BEGIN RSA PRIVATE KEY-----\n"
        "MIIEpAIBAAKCAQEA\n"
        "-----END RSA PRIVATE KEY-----"
    )
    redacted = redact_secrets(text)
    assert "MIIEpAIBAAKCAQEA" not in redacted
    assert "***REDACTED***" in redacted


def test_redact_secrets_leaves_plain_text_untouched():
    assert redact_secrets("tests passed: 12 ok") == "tests passed: 12 ok"


def test_command_result_snapshot_redacts_output():
    result = CommandResult(
        command="echo hi",
        exit_code=0,
        stdout="leaked ghs_abcdefghijklmnopqrstuvwxyz0000",
        stderr="key gho_abcdefghijklmnopqrstuvwxyz",
        duration_seconds=0.1,
    )
    snapshot = result.to_snapshot()
    assert "ghs_abcdefghijklmnopqrstuvwxyz0000" not in snapshot["stdout"]
    assert "gho_abcdefghijklmnopqrstuvwxyz" not in snapshot["stderr"]
    assert "***REDACTED***" in snapshot["stdout"]
