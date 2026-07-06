# Fix 03 — Vazamento de segredos e execução não isolada

Cobre **PA-11** (vazamento de `SESSION_SECRET`/`TOKEN_ENCRYPTION_KEY`), **PA-12** (RCE sem
sandbox), **PA-13** (comandos configuráveis + saída persistida) e **PA-14** (redação parcial).

> **Aplique PA-11 imediatamente.** É um patch de poucas linhas e fecha o vazamento mais grave.

---

## 1. `_safe_env`: trocar blocklist por allowlist (PA-11)

Hoje o subprocess herda **todo** o ambiente menos alguns prefixos — então `SESSION_SECRET` e
`TOKEN_ENCRYPTION_KEY` vazam. Inverta a lógica: passe apenas o mínimo necessário.

**Arquivo:** `backend/app/services/runner_service.py`

Remova `SECRET_ENV_PREFIXES`/`SECRET_ENV_NAMES` e substitua `_safe_env`:

```python
# Variáveis que o toolchain de build legitimamente precisa. NADA de segredos da app.
SAFE_ENV_ALLOWLIST = (
    "PATH",
    "HOME",
    "LANG",
    "LC_ALL",
    "TZ",
    "TMPDIR",
    "SHELL",
    # toolchains:
    "GOPATH", "GOCACHE", "GOMODCACHE",
    "NODE_ENV",
    "PYTHONUNBUFFERED", "PYTHONDONTWRITEBYTECODE",
)


def _safe_env() -> dict[str, str]:
    # Allowlist explícita: o processo não-confiável só vê o que está aqui.
    safe = {key: os.environ[key] for key in SAFE_ENV_ALLOWLIST if key in os.environ}
    # Garante PATH mesmo se ausente no processo pai.
    safe.setdefault("PATH", "/usr/local/bin:/usr/bin:/bin")
    return safe
```

Por que allowlist e não blocklist: qualquer segredo novo no `.env` (chave de API, secret de
sessão, etc.) passa a ser seguro por padrão. Com blocklist, todo segredo novo precisa lembrar
de ser adicionado — e este bug nasceu exatamente desse esquecimento.

**Teste de regressão (adicionar em `backend/tests/`):**

```python
import os
from app.services.runner_service import _safe_env

def test_safe_env_does_not_leak_app_secrets(monkeypatch):
    monkeypatch.setenv("SESSION_SECRET", "super-secret")
    monkeypatch.setenv("TOKEN_ENCRYPTION_KEY", "enc-key")
    monkeypatch.setenv("GITHUB_APP_PRIVATE_KEY", "pk")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-x")
    env = _safe_env()
    assert "SESSION_SECRET" not in env
    assert "TOKEN_ENCRYPTION_KEY" not in env
    assert "GITHUB_APP_PRIVATE_KEY" not in env
    assert "OPENAI_API_KEY" not in env
    assert "PATH" in env
```

---

## 2. Redigir a saída persistida (PA-13, PA-14)

`stdout`/`stderr` são salvos no snapshot e podem ir para comentários do GitHub. Redija padrões
de segredo antes de persistir.

**Arquivo:** `backend/app/services/runner_service.py`

```python
import re

_SECRET_PATTERNS = [
    re.compile(r"x-access-token:[^@\s]+@"),
    re.compile(r"\bghs_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bgho_[A-Za-z0-9]{20,}\b"),
    re.compile(r"-----BEGIN[ A-Z]*PRIVATE KEY-----.*?-----END[ A-Z]*PRIVATE KEY-----", re.S),
]

def redact_secrets(text: str) -> str:
    for pattern in _SECRET_PATTERNS:
        text = pattern.sub("***REDACTED***", text)
    return text
```

E aplique em `CommandResult.to_snapshot`:

```python
    def to_snapshot(self) -> dict:
        return {
            "command": redacted_command(self.command),
            "exit_code": self.exit_code,
            "stdout": redact_secrets(self.stdout[-4000:]),
            "stderr": redact_secrets(self.stderr[-4000:]),
            "duration_seconds": round(self.duration_seconds, 3),
            "timed_out": self.timed_out,
        }
```

---

## 3. Isolar a execução (PA-12) — a parte que exige decisão de arquitetura

A allowlist de env reduz o vazamento, mas **não** isola a execução de código não-confiável.
Escolha uma das duas posturas (ver `README.md`):

### Opção A — sandbox por run (worker dedicado)

No worker (fix 02), execute cada análise em container efêmero com:

- usuário **não-root**, sem capabilities;
- **sem credenciais de infra** montadas (nada de role da cloud, nada de `DATABASE_URL`);
- egress de rede restrito — em especial **bloquear o IP de metadata** `169.254.169.254`
  (evita SSRF para credenciais da cloud);
- limites de CPU/memória/disco (`--cpus`, `--memory`, `--pids-limit`, quota de `/tmp`);
- timeout global do container alinhado ao `command_timeout_seconds`.

Esboço de `run_command` via container (substitui o `subprocess.run` direto no worker):

```python
completed = subprocess.run(
    [
        "docker", "run", "--rm",
        "--network", "sandbox-no-metadata",   # rede sem rota para 169.254.169.254
        "--user", "1000:1000",
        "--cpus", "2", "--memory", "2g", "--pids-limit", "512",
        "--read-only", "--tmpfs", "/work:size=512m",
        "-v", f"{cwd}:/work/repo:ro",
        "-w", "/work/repo",
        runner_image, "sh", "-c", command,
    ],
    env=_safe_env(), text=True, capture_output=True, timeout=timeout,
)
```

### Opção B — delegar ao GitHub Actions

Dispare um workflow no repositório do cliente; ele roda os gates e devolve o JSON via
`repository_dispatch` / API. A execução de código não-confiável passa a ocorrer na conta do
cliente — você deixa de hospedar o risco de PA-12 por completo.

---

## Checklist

- [ ] `_safe_env` por allowlist + teste de regressão (PA-11) — **imediato**
- [ ] `redact_secrets` aplicado em `to_snapshot` (PA-13, PA-14)
- [ ] Tratar `install_command`/`test_command` como input não-confiável; considerar templates por linguagem (PA-13)
- [ ] Isolamento de execução definido (sandbox container **ou** GitHub Actions) (PA-12)
