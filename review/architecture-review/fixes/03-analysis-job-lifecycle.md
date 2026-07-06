# AR-03 — Deepen Analysis Job lifecycle

## Tipo

Correcao de confiabilidade com impacto em disponibilidade, performance operacional e
seguranca contra abuso por jobs presos.

## Prioridade

Alta. O worker atual consegue deixar jobs permanentemente em `running` e a unique
constraint em `analysis_run_id` pode impedir re-enqueue futuro do mesmo run.

## Contexto

Automatic Pull Request Analysis e Manual Pull Request Analysis enfileiram um Analysis Run
em `analysis_jobs`. O worker chama `claim_next`, executa `execute_analysis_run` e registra
exception no log se algo escapar.

O model `AnalysisJob` possui `analysis_run_id`, `status` e `started_at`, mas nao possui
terminal state, retry count, error message, finished_at ou lease/heartbeat.

## Problema

O module `analysis_queue` e shallow: ele sabe enfileirar e reivindicar, mas nao sabe
concluir, falhar, reprocessar, expirar lease ou tornar a operacao idempotente por estado.

O worker tambem e shallow: ele pega um run, chama execution e engole exception no log. O
estado do job fica fora da locality da fila.

## Evidencias no codigo

- `backend/app/services/analysis_queue.py`
  - `enqueue` usa `ON CONFLICT (analysis_run_id) DO NOTHING`.
  - `claim_next` muda `status` para `running` e retorna `analysis_run_id`.
  - Nao existe `complete`, `fail`, `requeue`, `release` ou `claim_stale`.
- `backend/app/worker.py`
  - `process_next_job` captura `Exception`, loga e retorna `run_id`.
  - Nao atualiza o job para terminal state.
- `backend/app/models/analysis_job.py`
  - Nao ha `finished_at`, `last_error`, `attempt_count`, `locked_at` ou `locked_by`.
- `backend/tests/test_analysis_queue.py`
  - Cobre enqueue/claim/idempotencia simples.
  - Nao cobre falha, retry, completion ou job stale.

## Impacto

### Performance e disponibilidade

- Jobs podem ficar presos em `running` para sempre.
- Re-enqueue do mesmo Analysis Run pode ser bloqueado pela unique constraint.
- Um worker que morre depois de `claim_next` deixa trabalho perdido.
- A fila nao oferece backoff, retry nem observabilidade basica.

### Seguranca operacional

- Um usuario autorizado pode gerar custo e travar capacidade se jobs ficarem presos.
- Sem lease e retry policy, e dificil aplicar rate limit ou limites de tentativas por
  repository.

## Objetivo

Deepen o Analysis Job lifecycle para que enqueue, claim, complete, fail, retry e stale
reclaim sejam responsabilidades do mesmo module.

## Escopo tecnico

1. Estender schema de `analysis_jobs`.
   - `status`: `queued`, `running`, `completed`, `failed`, opcionalmente `cancelled`.
   - `attempt_count`: inteiro.
   - `started_at`: timestamp.
   - `finished_at`: timestamp.
   - `last_error`: texto opcional.
   - `locked_at`: timestamp opcional.
   - `locked_by`: texto opcional, se houver multiplos workers.

2. Ajustar unique/idempotencia.
   - Decidir se `analysis_run_id` continua unico.
   - Se continuar unico, `enqueue` deve reativar jobs terminal/stale quando o Analysis Run
     puder ser reexecutado.
   - Se nao continuar unico, a fila deve evitar duplicidade ativa por run.

3. Implementar operacoes de lifecycle.
   - `enqueue(analysis_run_id)`
   - `claim_next(worker_id=None)`
   - `complete(job_id ou analysis_run_id)`
   - `fail(job_id ou analysis_run_id, error_message, retryable=True)`
   - `requeue_stale(max_age)`

4. Atualizar worker.
   - Worker deve marcar completed quando `execute_analysis_run` retorna sem exception.
   - Worker deve marcar failed quando exception escapa.
   - Worker deve respeitar limite de tentativas.

5. Manter compatibilidade com `execute_analysis_run`.
   - Analysis Run continua sendo a fonte de Run Status e Gate Decision.
   - Analysis Job e o mecanismo operacional da fila.

## Fora de escopo

- Trocar Postgres por Redis/Celery.
- Adicionar UI de fila.
- Rate limiting completo por usuario/repository. Este ticket prepara o seam, mas nao
  precisa implementar quotas.

## Plano de implementacao sugerido

1. Criar migracao Alembic.
   - Adicionar colunas novas.
   - Popular `attempt_count=0` para registros existentes.
   - Criar indice em `(status, created_at)` e possivelmente `(status, started_at)`.

2. Refatorar `analysis_queue.claim_next`.
   - Retornar um objeto pequeno com `job_id` e `analysis_run_id`, nao apenas UUID.
   - Usar `FOR UPDATE SKIP LOCKED`.
   - Incrementar `attempt_count` ao claim.
   - Setar `started_at`/`locked_at`.

3. Implementar terminal transitions.
   - `complete(job_id)` seta `status='completed'`, `finished_at=now()`.
   - `fail(job_id, error)` seta `status='failed'`, `finished_at=now()`,
     `last_error=...`.
   - Se `attempt_count < max_attempts`, permitir `status='queued'` novamente.

4. Atualizar `worker.process_next_job`.
   - Capturar job object.
   - Chamar `complete` no sucesso.
   - Chamar `fail` no erro.
   - Logar job_id e analysis_run_id.

5. Tratar stale running jobs.
   - `claim_next` pode primeiro requeue jobs `running` com `started_at < now() - lease`.
   - Alternativamente criar funcao explicita chamada no loop do worker.

6. Atualizar testes.
   - Cobrir re-enqueue de job terminal.
   - Cobrir reclaim de job stale.
   - Cobrir exception no worker atualizando job failed.

## Criterios de aceite

- Nenhum job fica permanentemente `running` sem chance de reclaim.
- Worker marca job como `completed` apos execution bem-sucedida.
- Worker marca job como `failed` quando exception escapa.
- `enqueue` e idempotente para job ativo.
- `enqueue` permite nova tentativa quando o job anterior esta terminal ou stale, conforme
  regra definida.
- Testes cobrem sucesso, erro, idempotencia e stale reclaim.
- Rotas que enfileiram Analysis Run continuam retornando `202`.

## Plano de testes

Adicionar/ajustar:

- `backend/tests/test_analysis_queue.py`
  - `test_claim_next_returns_job_and_marks_running`
  - `test_complete_marks_job_completed`
  - `test_fail_marks_job_failed_and_records_error`
  - `test_enqueue_does_not_duplicate_active_job`
  - `test_enqueue_requeues_terminal_job_when_allowed`
  - `test_claim_next_reclaims_stale_running_job`
- `backend/tests/test_worker.py`
  - `test_process_next_job_marks_completed`
  - `test_process_next_job_marks_failed_on_exception`

Comando:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests\test_analysis_queue.py tests\test_worker.py tests\test_analysis_runs.py tests\test_github_webhooks.py
```

## Riscos

- Mudar unique/idempotencia pode criar execucoes duplicadas do mesmo Analysis Run.
- Retry automatico de erro nao-operacional pode desperdiçar recursos.
- Corrigir fila sem revisar `AnalysisRun.status` pode deixar estados inconsistentes.

## Mitigacoes

- Garantir no banco que so existe um job ativo por Analysis Run.
- Definir `max_attempts` baixo no MVP.
- Reusar validacoes de `execute_analysis_run` para bloquear runs fresh `running`.
- Logar transitions com job_id, analysis_run_id e status novo.

