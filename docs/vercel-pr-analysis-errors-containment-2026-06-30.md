# Verificacao Vercel - analise de PR, erros e contencao - 2026-06-30

Verificacao feita em 2026-06-30 para o projeto Vercel `quality-gate`
(`prj_4QZrVOAkyf2OPUzXK6V8USNL7WY8`) no time
`team_diFFtappPJzeg0YQVU1ysmAr`.

Escopo pedido: somente fluxo de analise de Pull Request.

## Resultado curto

Nao ha erro gerado pela parte de analise de PR nos logs Vercel retornados.

O que foi encontrado:

- Runtime errors agregados para rotas de analise nos ultimos 7 dias: nenhum.
- Logs de producao nas ultimas 24h por rota: somente `/server/api/auth/me` e
  `/server/health`.
- Logs de preview nas ultimas 24h: nenhum request de runtime.
- Busca por `analysis`, `analyze`, `pull-requests`, `webhooks`, `execute` e
  `publish-github`: nenhum log encontrado.
- 5xx no deployment de producao atual nas ultimas 24h: nenhum.
- 4xx no deployment de producao atual nas ultimas 24h: apenas
  `GET /server/api/auth/me 401`, fora do fluxo de analise de PR.
- Build logs dos deployments relacionados a PR analysis: sem erro; todos
  terminaram em `Build Completed`.

Interpretacao: o deploy esta saudavel do ponto de vista da Vercel, mas nao houve
trafego de analise de PR registrado no intervalo consultado. Portanto, nao existe
stack trace ou erro HTTP de analise para explicar nos logs. O maior risco atual e
operacional: o codigo enfileira analises, mas o processamento depende de um worker
separado que nao aparece configurado em `vercel.json`.

## Endpoints de analise cobertos

Endpoints mapeados no codigo local:

| Fluxo | Endpoint |
| --- | --- |
| Listar PRs | `GET /server/api/repositories/{repository_id}/pull-requests` |
| Capturar contexto do PR | `GET /server/api/repositories/{repository_id}/pull-requests/{pr_number}/context` |
| Analisar PR manualmente | `POST /server/api/repositories/{repository_id}/pull-requests/{pr_number}/analyze` |
| Listar analises | `GET /server/api/repositories/{repository_id}/analysis-runs` |
| Ver detalhe da analise | `GET /server/api/analysis-runs/{analysis_run_id}` |
| Reexecutar analise | `POST /server/api/analysis-runs/{analysis_run_id}/execute` |
| Publicar resultado no GitHub | `POST /server/api/analysis-runs/{analysis_run_id}/publish-github` |
| Webhook GitHub | `POST /server/api/github/webhooks` |

Nenhum desses endpoints apareceu nos runtime logs retornados para producao ou
preview nas ultimas 24h.

## Evidencias Vercel coletadas

### Runtime errors

Consulta: `get_runtime_errors` com rotas relacionadas a analise, ultimos 7 dias.

Resultado:

```text
No runtime errors found in the selected time range.
```

### Runtime por rota - producao, ultimas 24h

Resultado:

| Rota | Contagem |
| --- | ---: |
| `/server/api/auth/me` | 1 |
| `/server/health` | 1 |

Conclusao: nenhuma rota de analise de PR foi chamada ou registrada no periodo.

### Runtime por rota - preview, ultimas 24h

Resultado: nenhum request retornado.

### Buscas textuais em producao

| Termo | Resultado |
| --- | --- |
| `analysis` | Nenhum log encontrado |
| `analyze` | Nenhum log encontrado |
| `pull-requests` | Nenhum log encontrado |
| `webhooks` | Nenhum log encontrado no deployment atual |
| `execute` | Nenhum log encontrado no deployment atual |
| `publish-github` | Nenhum log encontrado no deployment atual |

### 4xx/5xx

Producao, deployment atual `dpl_Drtwn7HrqPkUoxCbVdYqXW3Vt3Vk`:

```text
4xx:
17:19:20 GET /server/api/auth/me 401 [info/serverless]

5xx:
No logs found for the specified criteria.
```

Esse `401` nao e erro de analise de PR. Ele vem do fluxo de autenticacao quando
nao existe cookie de sessao.

### Build logs dos deployments de PR analysis

Deployments verificados:

| Deployment | Ref/commit | Motivo | Resultado |
| --- | --- | --- | --- |
| `dpl_DYpnhF5J44xD6TMw5VKvYJdLzsqR` | `fix/pr-analysis-production-hardening`, `f1b6df2` | Relatorio HTML de fixes de PR analysis | Build OK |
| `dpl_Drtwn7HrqPkUoxCbVdYqXW3Vt3Vk` | `main`, `9cb9beb` | Merge PR #32 retry analysis on error | Build OK |
| `dpl_2GPHKHW1hecMrUj8mp7J4LgBzb9W` | `feat/retry-analysis-on-error`, `ffacc04` | Botao Analyze para PR com erro | Build OK |
| `dpl_4pxMdV3Y7G21NMUjKWtoCszJrjKz` | `main`, `503e614` | Merge PR #31 checkout de analise na Vercel | Build OK |
| `dpl_7MJPJQ79VL2yrbcKxgeayArFAgaU` | `codex/fix-production-pr-analysis-clone`, `df6cd5c` | Fetch de revisoes sem git binary | Build OK |

Todos os logs filtrados por erro mostraram `Build Completed in /vercel/output`.

## Erros observados

### Erro observado 1 - nenhum erro de analise registrado na Vercel

Severidade: informativa.

Nao ha erro de analise de PR nos logs Vercel consultados. Isso significa que a
Vercel nao registrou chamadas aos endpoints de analise, nem excecoes associadas a
eles, no periodo retornado.

Contencao:

1. Nao aplicar rollback baseado nos logs atuais; nao ha falha de deployment ou
   runtime de analise para reverter.
2. Gerar uma chamada controlada de analise em producao ou preview para criar
   evidencia observavel.
3. Acompanhar se o request `POST /server/api/repositories/{id}/pull-requests/{n}/analyze`
   aparece nos logs e se o job entra em `analysis_jobs`.

### Erro observado 2 - `401` em `/server/api/auth/me`, fora do escopo de analise

Severidade: baixa para analise de PR.

Log:

```text
GET /server/api/auth/me 401 [info/serverless]
```

Explicacao:

- O endpoint exige cookie de sessao.
- Um visitante anonimo sem `qg_session` recebe `401`.
- Esse erro nao passa por Analyze, webhook, queue, worker ou gates.

Contencao:

1. Tratar `401` do `/api/auth/me` como estado anonimo normal no frontend.
2. Manter alertas de analise filtrando rotas `/api/repositories`, `/api/analysis-runs`
   e `/api/github/webhooks`, para esse `401` nao contaminar o painel de incidentes
   de PR analysis.

## Risco critico relacionado - analise pode enfileirar sem executar

Severidade: alta.

Isto nao apareceu como erro Vercel, mas e o risco mais importante encontrado na
correlacao com o codigo.

Evidencia local:

- `backend/app/api/routes_repositories.py` cria analise manual e chama
  `analysis_queue.enqueue(run.id)`.
- `backend/app/api/routes_analysis.py` reexecuta analise chamando
  `analysis_queue.enqueue(analysis_run_id)`.
- `backend/app/services/github_webhook_service.py` enfileira analises novas de
  PR quando recebe webhook suportado.
- `backend/app/services/analysis_queue.py` grava jobs em `analysis_jobs`.
- `backend/app/worker.py` e o processo que chama `analysis_queue.claim_next()` e
  `analysis_execution_service.execute_analysis_run(...)`.
- `vercel.json` define apenas services `frontend` e `backend`, sem worker.

Impacto:

- A API pode responder `202` para uma analise, mas o job pode ficar `queued` se
  nenhum worker estiver rodando.
- Isso nao gera necessariamente erro nos logs da Vercel.
- O usuario ve a analise parada ou sem resultado.

Contencao imediata:

1. Verificar no banco se existem jobs parados:

```sql
select status, count(*), min(created_at), max(created_at)
from analysis_jobs
group by status
order by status;

select id, analysis_run_id, status, created_at, started_at
from analysis_jobs
where status in ('queued', 'running')
order by created_at;
```

2. Se houver jobs `queued`, iniciar temporariamente o worker em ambiente com acesso
   ao mesmo banco e secrets:

```powershell
cd backend
python -m app.worker
```

3. Se houver jobs `running` antigos sem worker ativo, voltar para `queued` ou marcar
   a analise como `error`, conforme decisao operacional:

```sql
update analysis_jobs
set status = 'queued', started_at = null
where status = 'running'
  and started_at < now() - interval '30 minutes';
```

4. Para qualquer analise impactada, registrar `error_message` claro em
   `analysis_runs` se nao for possivel reprocessar.

Correcao definitiva:

1. Implantar `backend/app/worker.py` como worker persistente fora da Vercel
   Functions ou em plataforma que suporte processo de longa duracao.
2. Separar a API Vercel do runner de analise.
3. Adicionar heartbeat do worker e alerta para jobs parados.

## Plano de contencao imediata

Use este plano quando o usuario relatar que a analise de PR nao executa, fica
parada, ou volta com erro.

1. Confirmar se houve request HTTP:
   - Procurar nos logs Vercel por `/server/api/repositories/*/pull-requests/*/analyze`.
   - Procurar por `/server/api/github/webhooks`.
   - Se nao houver log, problema esta antes da API: frontend, auth, webhook URL,
     rota errada ou evento nao disparado.

2. Confirmar se a API criou run/job:
   - Consultar `analysis_runs` pelo `repository_id`, `pr_number` e `head_sha`.
   - Consultar `analysis_jobs` pelo `analysis_run_id`.
   - Se existe run sem job, reexecutar pelo endpoint `/execute` ou inserir job.

3. Confirmar se o worker esta ativo:
   - Se `analysis_jobs.status = queued` cresce, worker nao esta consumindo.
   - Se `running` fica antigo, worker travou ou morreu durante execucao.

4. Conter sem perder dados:
   - Nao apagar `analysis_runs`.
   - Reenfileirar jobs `running` antigos somente depois de confirmar que nao ha
     worker ativo processando o mesmo job.
   - Marcar erro operacional com mensagem explicita quando nao for seguro rerodar.

5. Reduzir impacto para usuario:
   - Mostrar estado "Queued" e "Worker unavailable" na UI quando a fila estiver
     parada.
   - Permitir Retry apenas para runs `ERROR` ou `PENDING` stale.
   - Publicar no GitHub somente runs `COMPLETED` ou `ERROR` com relatorio gerado.

## Contencao preventiva para erros futuros

| Possivel erro futuro | Sinal esperado | Contencao automatica | Correcao estrutural |
| --- | --- | --- | --- |
| Worker nao esta rodando | Jobs `queued` antigos | Alerta quando `queued` > 5 min | Worker persistente com health/heartbeat |
| Worker travou no meio | Jobs `running` antigos | Reenfileirar apos SLA e registrar tentativa | Lock com lease/timeout e retry controlado |
| Webhook secret ausente | `503 github_webhook_secret_missing` | Bloquear deploy sem secret | Validacao de env em startup |
| Assinatura webhook invalida | `401 github_webhook_signature_invalid` | Nao processar payload e logar delivery id | Conferir secret e redelivery no GitHub |
| Evento PR ignorado | Resposta `ignored=true` | Registrar `reason` em log estruturado | Dashboard de eventos ignorados |
| Repositorio desconhecido | `unknown_repository` | Sugerir sincronizar instalacao | Sync automatico em evento installation |
| Falha ao capturar contexto do PR | Run `ERROR` com erro de enrichment | Criar run de erro e permitir Retry | Verificar permissoes do GitHub App |
| Checkout de SHA falha | `Repository checkout failed` | Marcar gate como erro e permitir Retry | Usar GitHub archive com token e log de HTTP |
| Coverage install falha | `Coverage install command failed` | Guardar stdout/stderr redigidos | Config por repositorio e preflight command |
| Coverage report ausente | `Coverage report was not produced` | Marcar coverage error e mostrar comando | Validar `report_path` antes de executar |
| Semgrep timeout | `semgrep timed out` | Encerrar gate com erro controlado | Runner com recursos e timeout por scanner |
| Semgrep sem JSON | `semgrep output was empty/not parseable JSON` | Capturar stderr e versao do scanner | Pin de versao e preflight do scanner |
| Diff ausente | `Pull Request diff evidence is required` | Rebuscar contexto do PR | Persistir fallback de patches por arquivo |
| Timeout de plataforma | Funcao encerrada antes de gravar erro | Rodar analise fora da Vercel Functions | Worker dedicado; API so enfileira |
| Cold start pesado | Logs baixando `semgrep` em request HTTP | Remover scanners da API | Separar dependencias API/worker |
| OpenAI indisponivel | AI review `skipped` ou erro | Continuar gates deterministicos | Retry/backoff e circuit breaker |
| Publicacao GitHub falha | Erro em `publish-github` | Manter relatorio local e permitir retry | Validar permissoes `pull_requests`/`statuses` |

## Logs estruturados recomendados

Adicionar logs JSON, sem secrets, nos pontos abaixo:

```text
analysis.enqueue
analysis.claim_next
analysis.started
analysis.coverage.started
analysis.coverage.completed
analysis.security.started
analysis.security.completed
analysis.technical_debt.started
analysis.technical_debt.completed
analysis.ai_review.started
analysis.ai_review.completed
analysis.completed
analysis.failed
webhook.received
webhook.ignored
webhook.analysis_created
```

Campos minimos:

```json
{
  "event": "analysis.started",
  "analysis_run_id": "...",
  "repository_id": "...",
  "pr_number": 123,
  "head_sha": "...",
  "trigger_source": "manual",
  "job_id": "...",
  "attempt": 1
}
```

Campos de erro:

```json
{
  "event": "analysis.failed",
  "analysis_run_id": "...",
  "gate": "coverage",
  "error_code": "coverage_report_missing",
  "message": "Coverage report was not produced.",
  "duration_ms": 123456
}
```

Nao logar:

- Installation tokens.
- OAuth tokens.
- Private keys.
- Webhook secret.
- `GITHUB_APP_PRIVATE_KEY`.
- `OPENAI_API_KEY`.
- Conteudo completo de arquivos analisados.

## Alertas recomendados

1. `analysis_jobs queued > 0` por mais de 5 minutos.
2. `analysis_jobs running` por mais de 30 minutos.
3. Taxa de `analysis_runs.status = error` acima de 20% em 1h.
4. Qualquer `5xx` em `/server/api/repositories/*/pull-requests/*/analyze`.
5. Qualquer `5xx` em `/server/api/github/webhooks`.
6. Qualquer `github_webhook_secret_missing`.
7. Cold start de API contendo `Downloading semgrep`.

## Acao recomendada agora

1. Nao fazer rollback: nao ha erro de analise de PR nos logs Vercel.
2. Executar uma analise controlada em preview ou producao para gerar trilha real.
3. Confirmar no banco se ha jobs `queued` ou `running` antigos.
4. Subir o worker de analise como processo persistente.
5. Separar dependencias de API e worker para remover scanners do runtime HTTP.
6. Implementar logs estruturados e alertas acima antes de nova rodada de testes.

## Ferramentas usadas

- Vercel connector:
  - `get_deployment`
  - `list_deployments`
  - `get_runtime_errors`
  - `get_runtime_logs`
  - `get_deployment_build_logs`
- Arquivos locais revisados:
  - `.vercel/project.json`
  - `backend/app/api/routes_repositories.py`
  - `backend/app/api/routes_analysis.py`
  - `backend/app/services/github_webhook_service.py`
  - `backend/app/services/analysis_queue.py`
  - `backend/app/worker.py`
  - `backend/app/services/analysis_execution_service.py`
  - `backend/app/services/gates/coverage_gate.py`
  - `backend/app/services/gates/security_gate.py`
  - `backend/app/services/gates/technical_debt_gate.py`
  - `backend/app/models/analysis_job.py`
  - `backend/app/models/analysis_run.py`

