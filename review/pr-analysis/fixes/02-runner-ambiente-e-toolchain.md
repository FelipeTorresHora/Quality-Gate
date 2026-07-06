# Fix 02 — Runtime com toolchain e filesystem gravável

Cobre **PA-01** (serverless sem `npm`/`go`/`git`/scanners, FS read-only) e **PA-03**
(`command_timeout_seconds` > `maxDuration`).

## O problema em uma frase

O `backend/Dockerfile` instala `git`, `golang-go`, `nodejs`, `npm` — mas a **Vercel não usa
esse Dockerfile**. Em produção o backend roda como função Python serverless, sem esses binários
e com disco somente-leitura. O pipeline de análise não tem como rodar ali.

## 1. Onde a análise deve rodar

Hospede o **worker** (do fix 01) no container do `backend/Dockerfile`, que já tem o toolchain,
num provedor que roda containers de longa duração (Fly.io, Railway, Render, ECS, etc.).
Resultado:

- a **app web** (FastAPI servindo as rotas) pode continuar onde está;
- o **worker** roda no container com `git`/`npm`/`go`/scanners e `/tmp` gravável;
- nada de pesado roda na função serverless.

Garanta que os scanners Python tenham binário no `PATH` do container. Eles já estão em
`requirements.txt` (`bandit`, `detect-secrets`, `pip-audit`, `semgrep`), então `pip install`
cria os entry-points — confirme com um teste de smoke no container:

```dockerfile
# após o pip install, no backend/Dockerfile:
RUN semgrep --version && bandit --version && detect-secrets --version && pip-audit --version
```

> Para repositórios **JS/TS/Go**, o worker precisa de `node`/`npm`/`go` — já presentes no
> Dockerfile. Se for suportar mais linguagens, adicione os toolchains aqui (ou use a Opção B,
> GitHub Actions, onde o toolchain é responsabilidade do runner do cliente).

## 2. Introduzir uma fronteira `Runner` (PA-18, destrava PA-01)

Hoje os gates importam `RunnerWorkspace` e montam shell direto. Defina uma interface para poder
trocar "subprocess local" por "container sandbox" ou "GitHub Actions" sem reescrever os gates.

**Novo:** `backend/app/services/gates/runner_protocol.py`

```python
from typing import Protocol
from app.services.runner_service import CommandResult

class Runner(Protocol):
    repo_path: "Path"
    def checkout(self, revision: str) -> None: ...
    def run(self, command: str, working_directory: str = ".") -> CommandResult: ...
```

`RunnerWorkspace` já satisfaz esse Protocol. Os gates passam a receber um `Runner` injetado
(criado uma vez por análise — ver fix 04, checkout único) em vez de instanciar o próprio
`RunnerWorkspace`. Para sandbox/Actions, basta uma nova implementação do Protocol.

## 3. Alinhar timeouts (PA-03)

O teto de um comando nunca pode ser maior que o teto do runtime que o hospeda. Com worker
durável, não há mais `maxDuration` de 300s, mas ainda é preciso um teto global por análise.

**Arquivo:** `backend/app/core/config.py`

```python
command_timeout_seconds: int = 300       # por comando individual
analysis_total_timeout_seconds: int = 900  # teto da análise inteira (todos os gates)
```

E aplique um deadline global no worker/`execute_analysis_run`:

```python
import time
deadline = time.monotonic() + get_settings().analysis_total_timeout_seconds
# antes de cada gate:
if time.monotonic() > deadline:
    return _finish_with_error(db, run, "Analysis exceeded total time budget.")
```

Se mantiver **qualquer** execução na função serverless (não recomendado), então
`command_timeout_seconds` **tem** que ser menor que `maxDuration` da `vercel.json`.

## 4. `vercel.json`: deixar claro que o backend serverless não executa análise

Com o worker assumindo o pipeline, a função serverless só serve rotas rápidas. Documente/ reduza
expectativas — `maxDuration` alto ali vira desnecessário para a análise (mas mantenha o que as
rotas de leitura precisam).

## Checklist

- [ ] Worker rodando no container do `backend/Dockerfile` (com toolchain), fora do serverless
- [ ] Smoke-test dos binários de scanner no build
- [ ] Interface `Runner` (Protocol) e gates recebendo o runner injetado
- [ ] `command_timeout_seconds` ≤ teto do runtime; `analysis_total_timeout_seconds` aplicado
- [ ] Decisão registrada: worker container (A) ou GitHub Actions (B)
