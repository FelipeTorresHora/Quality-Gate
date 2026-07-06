# Fix 01 — Tirar o pipeline da requisição HTTP

Cobre **PA-02** (pipeline síncrono na request → timeout) e **PA-04** (BackgroundTasks morto em
serverless). É a mudança que efetivamente conserta o "erro em produção".

## Princípio

A rota de análise deve **apenas enfileirar** o run e responder `202 Accepted` na hora. Um
**worker durável** (processo separado, fora do serverless) consome a fila e executa
`execute_analysis_run`. O frontend faz **polling** do status.

```
POST /analyze ──> cria AnalysisRun (PENDING) ──> enfileira job ──> 202 {run_id}
                                                       │
                              worker (container)  <────┘  executa pipeline, atualiza status
frontend ──> GET /analysis-runs/{id} (polling até COMPLETED/ERROR)
```

## 1. Rota: enfileirar em vez de executar

**Arquivo:** `backend/app/api/routes_repositories.py`

```python
@router.post("/{repository_id}/pull-requests/{pr_number}/analyze",
             response_model=AnalysisRunDetail, status_code=202)
def analyze_pull_request(repository_id, pr_number, _csrf=Depends(require_csrf_token),
                         db=Depends(get_db), current_user=Depends(get_current_user)):
    require_repository_access(db, current_user, repository_id)
    context = github_service.get_repository_pull_request_context(db, repository_id, pr_number)
    run = analysis_service.create_or_reuse_manual_analysis_run(db, repository_id, context)
    if run.status == AnalysisRunStatus.PENDING:
        analysis_queue.enqueue(run.id)   # <-- enfileira, NÃO executa aqui
    return analysis_service.get_analysis_run(db, run.id)
```

Faça o mesmo em `routes_analysis.execute_analysis_run` (enfileira) e em
`github_webhook_service` — substitua **tanto** o ramo `background_tasks.add_task` **quanto** o
ramo síncrono por `analysis_queue.enqueue(run.id)`.

## 2. Fila

Use a infra que você já tem. Como já existe **Postgres**, a opção de menor dependência é uma
fila no próprio banco (sem precisar subir Redis/Celery):

**Novo módulo:** `backend/app/services/analysis_queue.py`

```python
from uuid import UUID
from sqlalchemy import text
from app.db.session import SessionLocal

def enqueue(analysis_run_id: UUID) -> None:
    with SessionLocal() as db:
        db.execute(
            text("INSERT INTO analysis_jobs (analysis_run_id, status) "
                 "VALUES (:rid, 'queued') ON CONFLICT (analysis_run_id) DO NOTHING"),
            {"rid": str(analysis_run_id)},
        )
        db.commit()

def claim_next() -> UUID | None:
    # SKIP LOCKED garante que dois workers não pegam o mesmo job.
    with SessionLocal() as db:
        row = db.execute(text(
            "UPDATE analysis_jobs SET status='running', started_at=now() "
            "WHERE id = (SELECT id FROM analysis_jobs WHERE status='queued' "
            "           ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 1) "
            "RETURNING analysis_run_id")).first()
        db.commit()
        return UUID(str(row[0])) if row else None
```

> Crie a tabela `analysis_jobs` (id, analysis_run_id único, status, created_at, started_at) via
> `alembic revision --autogenerate` — siga `backend/CLAUDE.md` ("Adding a new resource").
>
> Alternativas equivalentes: Redis + RQ/Celery, ou um serviço gerenciado de filas. O padrão
> "enqueue na request, processa no worker" é o mesmo.

## 3. Worker

**Novo módulo:** `backend/app/worker.py`

```python
import time, logging
from app.services import analysis_queue, analysis_execution_service
from app.db.session import SessionLocal

log = logging.getLogger("analysis-worker")

def run_forever(poll_seconds: float = 2.0) -> None:
    while True:
        run_id = analysis_queue.claim_next()
        if run_id is None:
            time.sleep(poll_seconds)
            continue
        db = SessionLocal()
        try:
            analysis_execution_service.execute_analysis_run(db, run_id)
        except Exception:
            log.exception("analysis run %s failed", run_id)  # try/finally garante ERROR (fix 04)
        finally:
            db.close()

if __name__ == "__main__":
    run_forever()
```

Rode o worker como **processo separado** num runtime com toolchain (ver fix 02), por exemplo
`python -m app.worker`. **Não** rode na função serverless da Vercel.

## 4. Frontend: polling

Hoje `analyzePullRequest` espera o resultado final. Passe a tratar `202` e fazer polling:

**Arquivo:** `frontend/src/api/client.ts` (a função `analyzePullRequest` já existe; a página é
quem precisa pollar). Na página que dispara a análise:

```ts
async function startAnalysis(repoId: string, prNumber: number) {
  const run = await analyzePullRequest(repoId, prNumber); // agora retorna PENDING/RUNNING
  let current = run;
  while (current.status === "pending" || current.status === "running") {
    await new Promise((r) => setTimeout(r, 3000));
    current = await getAnalysisRun(current.id);
  }
  return current; // completed | error
}
```

Mantenha o padrão "fetch em `useEffect`/`useState`, re-fetch manual" do `frontend/CLAUDE.md` —
não introduza React Query só por isso.

## Adaptação para GitHub Actions (Opção B do README)

Se for delegar a execução: o "worker" vira um disparador de `workflow_dispatch` e um endpoint
que recebe o resultado (`POST /api/analysis-runs/{id}/result`, autenticado), em vez de rodar o
pipeline localmente. A separação request → fila → processamento assíncrono continua igual.

## Checklist

- [ ] Rotas `analyze` / `execute` e webhook só **enfileiram** (`202`)
- [ ] Tabela `analysis_jobs` + migração
- [ ] `analysis_queue` com `FOR UPDATE SKIP LOCKED`
- [ ] `app/worker.py` rodando como processo separado com toolchain
- [ ] Frontend faz polling do status
- [ ] Remover o uso de `BackgroundTasks` no webhook (PA-04)
