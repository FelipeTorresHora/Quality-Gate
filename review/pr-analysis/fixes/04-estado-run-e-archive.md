# Fix 04 — Estado do run preso e download de repo privado

Cobre **PA-06** (run preso em `RUNNING`), **PA-05** (download de archive privado falha) e
**PA-15** (cleanup transacional + duplicação de `create_or_reuse_*`).

---

## 1. `try/finally` no pipeline + recuperação de runs presos (PA-06)

Hoje, qualquer exceção (ou kill por timeout) depois de `status = RUNNING` deixa o run preso, e
o guard de entrada só aceita `PENDING`/`ERROR`.

### 1a. Permitir re-execução de runs `RUNNING` antigos (stale)

**Arquivo:** `backend/app/services/analysis_execution_service.py`

```python
from datetime import timedelta

STALE_RUNNING_AFTER = timedelta(minutes=30)

def execute_analysis_run(db, analysis_run_id):
    run = _get_run_for_execution(db, analysis_run_id)
    is_stale_running = (
        run.status == AnalysisRunStatus.RUNNING
        and run.started_at is not None
        and datetime.now(UTC) - run.started_at > STALE_RUNNING_AFTER
    )
    if run.status not in (AnalysisRunStatus.PENDING, AnalysisRunStatus.ERROR) and not is_stale_running:
        raise AppError(409, "analysis_run_not_pending",
                       "Only pending or errored analysis runs can be executed.")
    ...
```

### 1b. Garantir que o estado sempre fecha

Envolva o corpo do pipeline (do `status = RUNNING` em diante) para que toda exceção vire `ERROR`:

```python
    now = datetime.now(UTC)
    run.status = AnalysisRunStatus.RUNNING
    ...
    db.commit()

    try:
        gate_results = []
        # ... toda a execução dos gates + IA + relatório final ...
        run.finished_at = datetime.now(UTC)
        db.commit()
        return _get_run_for_execution(db, run.id)
    except AppError:
        raise
    except Exception as exc:
        db.rollback()
        return _finish_with_error(db, run, f"Unexpected analysis failure: {exc}")
```

> O worker (fix 01) também tem `try/except` em volta, mas o `_finish_with_error` aqui é o que
> registra a mensagem no run e marca `ERROR` — sem ele o worker só loga e o run fica preso.

---

## 2. Download de tarball de repositório privado (PA-05)

Bater direto no `codeload` com `Authorization: Bearer` falha (404) em repos privados. Use o
endpoint da API que **redireciona** para uma URL assinada do `codeload`.

**Arquivo:** `backend/app/services/runner_service.py`, em `download_repository_archive`:

```python
# Antes:
# archive_url = f"https://codeload.github.com/{owner}/{name}/tar.gz/{revision}"

# Depois — endpoint oficial que devolve 302 para o codeload assinado:
archive_url = (
    f"https://api.github.com/repos/{repository.owner}/"
    f"{repository.name}/tarball/{revision}"
)
```

Ponto importante de segurança/corretude no **redirect**: o `urllib` reenvia headers ao seguir
o `302`, e a URL assinada do `codeload` **não deve** receber o `Authorization` (o token já está
na query string assinada; reenviar o Bearer pode causar 400/conflito). Controle o redirect:

```python
class _NoAuthOnRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        new = super().redirect_request(req, fp, code, msg, headers, newurl)
        if new is not None:
            new.headers.pop("Authorization", None)  # não vaza o Bearer para o host assinado
        return new

_opener = urllib.request.build_opener(_NoAuthOnRedirect)

# usar _opener.open(request, timeout=timeout) no lugar de urllib.request.urlopen(...)
```

**Teste:** rodar a análise em um repositório **privado** e confirmar que
`coverage_result_json.commands[]` não traz `HTTP 404` no passo de download.

---

## 3. Remover duplicação de `create_or_reuse_*` (PA-15)

`create_or_reuse_webhook_analysis_run` e `create_or_reuse_manual_analysis_run` só diferem no
`trigger_source`. Extraia o builder comum.

**Arquivo:** `backend/app/services/analysis_service.py`

```python
def _build_pending_run(repository_id, context_model, trigger_source) -> AnalysisRun:
    return AnalysisRun(
        repository_id=repository_id,
        pr_number=context_model.pull_request.number,
        head_sha=context_model.pull_request.head_sha,
        status=AnalysisRunStatus.PENDING,
        decision=None,
        trigger_source=trigger_source,
        score=None,
        coverage_result_json={}, security_result_json={},
        technical_debt_result_json={}, ai_review_json={},
        pull_request_snapshot_json=context_model.pull_request.model_dump(mode="json"),
        changed_files_snapshot_json=[
            cf.model_dump(mode="json") for cf in context_model.changed_files
        ],
        diff_snapshot=context_model.diff_snapshot,
        diff_truncated=context_model.diff_truncated,
        final_report_markdown=None, error_message=None,
        started_at=None, finished_at=None,
    )

def create_or_reuse_manual_analysis_run(db, repository_id, context):
    return _create_or_reuse(db, repository_id, _coerce_context(context),
                            AnalysisTriggerSource.MANUAL)

def create_or_reuse_webhook_analysis_run(db, repository_id, context):
    return _create_or_reuse(db, repository_id, _coerce_context(context),
                            AnalysisTriggerSource.GITHUB_WEBHOOK)

def _create_or_reuse(db, repository_id, context_model, trigger_source):
    existing = get_analysis_run_by_pr_head(
        db, repository_id, context_model.pull_request.number,
        context_model.pull_request.head_sha)
    if existing is not None:
        return get_analysis_run(db, existing.id)
    return _commit_new_run_or_reuse(
        db, _build_pending_run(repository_id, context_model, trigger_source))
```

## Checklist

- [ ] `try/except` em volta do pipeline → `_finish_with_error` em qualquer exceção (PA-06)
- [ ] Re-execução de runs `RUNNING` stale liberada (PA-06)
- [ ] Download via `/repos/{owner}/{repo}/tarball/{ref}` + drop do `Authorization` no redirect (PA-05)
- [ ] Teste em repositório privado
- [ ] Builder `_build_pending_run` compartilhado (PA-15)
