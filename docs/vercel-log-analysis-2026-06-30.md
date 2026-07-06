# Diagnostico dos logs da Vercel - 2026-06-30

Analise feita em 2026-06-30, usando o conector Vercel no projeto `quality-gate`.
O ambiente local esta vinculado ao projeto Vercel por `.vercel/project.json` e usa
Vercel Services em `vercel.json`, com:

- `frontend`: entrypoint `frontend`, rota `/`.
- `backend`: entrypoint `backend/main.py`, rota `/server`, `maxDuration: 300`.
- Framework Vercel detectado: `services`.
- Deployment de producao atual: `dpl_Drtwn7HrqPkUoxCbVdYqXW3Vt3Vk`.
- Aliases de producao no deployment atual: `quality-gate-gamma.vercel.app`,
  `quality-gate-felipetorreshoras-projects.vercel.app`,
  `quality-gate-git-main-felipetorreshoras-projects.vercel.app`.

## Resumo executivo

Nao ha erro de build nos 12 deployments retornados pela Vercel. Todos chegaram a
`READY` e todos os build logs filtrados por erro terminaram com `Build Completed`.

Nao ha clusters de excecao de runtime no periodo consultado. Nas ultimas 24h de
runtime em producao, a Vercel registrou apenas duas rotas serverless:

| Rota | Status | Contagem | Interpretacao |
| --- | ---: | ---: | --- |
| `/server/health` | 200 | 1 | Backend respondeu corretamente. |
| `/server/api/auth/me` | 401 | 1 | Sessao anonima sem cookie `qg_session`; esperado pela implementacao atual. |

Os problemas reais encontrados sao operacionais/arquiteturais:

1. O backend enfileira analises, mas o worker que processa `analysis_jobs` nao esta
   definido em `vercel.json`. Sem outro processo rodando `backend/app/worker.py`, as
   analises ficam enfileiradas e nao aparecem como erro nos logs da Vercel.
2. O backend serverless carrega dependencias de scanner, especialmente `semgrep`.
   O build mostrou bundle Python de aproximadamente 423 MB e o runtime instala
   `semgrep` no cold start.
3. O frontend trata o `401` normal de `/api/auth/me` como erro visual na tela de
   login, embora isso seja apenas "usuario nao autenticado".
4. `vercel.json` limita o backend a 300s, enquanto a aplicacao permite budget total
   de analise de 900s. Se a analise rodar dentro de uma funcao Vercel, a plataforma
   pode interromper antes do timeout da propria aplicacao.

## Escopo dos logs consultados

- Deployments: todos os 12 deployments retornados por `list_deployments`.
- Build logs: `get_deployment_build_logs(errorsOnly=true)` nos 12 deployments.
- Build tail completo: deployment de producao atual e preview mais recente.
- Runtime errors: agregador de erros nos ultimos 7 dias e na ultima hora.
- Runtime logs: producao e preview nas ultimas 24h; producao na ultima hora.
- Runtime por rota: producao nas ultimas 24h.
- Validacao externa: `GET https://quality-gate-gamma.vercel.app/server/health`
  retornou `200 {"status":"ok"}` e a raiz retornou o HTML do frontend.

Observacao: a consulta bruta ampla de runtime pode ser limitada pela retencao do
plano Vercel. A propria ferramenta retornou aviso de retencao para janelas grandes
e uma busca textual ampla por `webhooks` estourou o tempo. As conclusoes abaixo
usam os logs efetivamente retornados, mais a correlacao com o codigo local.

## Inventario de deployments

| Criado em BRT | Target | Deployment | Ref | SHA | Resultado do build |
| --- | --- | --- | --- | --- | --- |
| 2026-06-30 12:10:05 | preview | `dpl_DYpnhF5J44xD6TMw5VKvYJdLzsqR` | `fix/pr-analysis-production-hardening` | `f1b6df2` | OK |
| 2026-06-30 11:17:22 | production | `dpl_Drtwn7HrqPkUoxCbVdYqXW3Vt3Vk` | `main` | `9cb9beb` | OK |
| 2026-06-30 11:16:55 | preview | `dpl_2GPHKHW1hecMrUj8mp7J4LgBzb9W` | `feat/retry-analysis-on-error` | `ffacc04` | OK |
| 2026-06-30 10:32:58 | production | `dpl_4pxMdV3Y7G21NMUjKWtoCszJrjKz` | `main` | `503e614` | OK |
| 2026-06-30 10:31:36 | preview | `dpl_7MJPJQ79VL2yrbcKxgeayArFAgaU` | `codex/fix-production-pr-analysis-clone` | `df6cd5c` | OK |
| 2026-06-30 09:37:48 | production | `dpl_9cMDiPUSX73YLetaGCWu7ZF87TEQ` | `main` | `8570c8e` | OK |
| 2026-06-30 09:36:15 | preview | `dpl_DGV4amLWUyXcV7C7r9UEuSfSkiJ4` | `codex/deploy-uncommitted-20260630` | `2f16ce4` | OK |
| 2026-06-30 09:35:38 | preview | `dpl_AdA9UHZ8agJu4dHAiPpecs4J13dF` | `codex/deploy-uncommitted-20260630` | `2f16ce4` | OK |
| 2026-06-29 21:28:25 | production | `dpl_6DGAupSYGpuYWUpb4h4hm2vQM8bW` | `codex/mvp-completion-hardening` | `3bd5ffa` | OK, `gitDirty=1` |
| 2026-06-29 21:23:41 | production | `dpl_H35GYJmcYQEU3VfVHV2jP3y6ZtGi` | `codex/mvp-completion-hardening` | `3bd5ffa` | OK, `gitDirty=1` |
| 2026-06-29 21:20:47 | production | `dpl_8H2K9GExyFDTHgb93RAoc2Lt13Ra` | `codex/mvp-completion-hardening` | `3bd5ffa` | OK, `gitDirty=1` |
| 2026-06-29 21:18:48 | production | `dpl_Diuwq7QNoWCjxBEdCxVwwo413yei` | `codex/mvp-completion-hardening` | `3bd5ffa` | OK, `gitDirty=1` |

## Evidencias de build

Todos os 12 deployments filtrados por `errorsOnly=true` mostraram apenas:

- `Vercel CLI 54.18.x`
- `Build Completed in /vercel/output`

O production atual (`dpl_Drtwn7HrqPkUoxCbVdYqXW3Vt3Vk`) mostrou:

- Build em `iad1`.
- Clone de `main`, commit `9cb9beb`.
- `npm run build` no frontend: `tsc -b && vite build`.
- Vite transformou 55 modulos e gerou JS de aproximadamente 267 kB gzip 81 kB.
- Python 3.12 via `backend/.python-version`.
- `uv 0.10.11`.
- `Bundle size (423.29 MB) exceeds the standard size; optimizing dependencies.`
- `Build Completed in /vercel/output [8s]`.
- Build cache enviado com aproximadamente 135 MB.

O preview mais recente (`dpl_DYpnhF5J44xD6TMw5VKvYJdLzsqR`) mostrou o mesmo padrao:

- Clone de `fix/pr-analysis-production-hardening`, commit `f1b6df2`.
- Frontend build OK.
- Python 3.12 e `uv 0.10.11`.
- `Bundle size (423.32 MB) exceeds the standard size; optimizing dependencies.`
- `Build Completed in /vercel/output [11s]`.

Conclusao: o deploy nao esta falhando no build. O alerta relevante e tamanho do
bundle Python.

## Evidencias de runtime

Agregador de runtime errors:

- Ultimos 7 dias: nenhum cluster de erro de runtime encontrado.
- Ultima hora: nenhum cluster de erro de runtime encontrado.

Runtime logs de producao na ultima hora:

```text
17:29:06 GET /server/health 200 [info/serverless]
dep=dpl_Drtwn7HrqPkUoxCbVdYqXW3Vt3Vk branch=main cache=MISS
Installing runtime dependencies...
Using CPython 3.12.13 interpreter at: /var/lang/bin/python3.12
Creating virtual environment at: /tmp/_vc_deps
Downloading semgrep (65.6MiB)
Installed 1 package in 10ms
+ semgrep==1.168.0
Runtime dependencies installed in 1.81s

17:19:20 GET /server/api/auth/me 401 [info/serverless]
dep=dpl_Drtwn7HrqPkUoxCbVdYqXW3Vt3Vk branch=main cache=MISS
Installing runtime dependencies...
Using CPython 3.12.13 interpreter at: /var/lang/bin/python3.12
Creating virtual environment at: /tmp/_vc_deps
Downloading semgrep (65.6MiB)
Installed 1 package in 10ms
+ semgrep==1.168.0
Runtime dependencies installed in 1.83s
```

Runtime por rota nas ultimas 24h:

| Rota | Contagem |
| --- | ---: |
| `/server/api/auth/me` | 1 |
| `/server/health` | 1 |

Preview runtime nas ultimas 24h: nenhum log encontrado.

Conclusao: producao responde, mas cold starts instalam dependencias pesadas.
Nao ha evidencia de execucao real de analise, webhook ou worker no intervalo
consultado.

## Achado 1 - Worker de analise nao esta implantado

Severidade: alta.

Evidencia local:

- `backend/app/api/routes_repositories.py` e `backend/app/api/routes_analysis.py`
  chamam `analysis_queue.enqueue(...)` e retornam `202`.
- `backend/app/services/analysis_queue.py` grava jobs em `analysis_jobs`.
- `backend/app/worker.py` contem `run_forever()` e chama
  `analysis_execution_service.execute_analysis_run(...)`.
- `vercel.json` define apenas os services `frontend` e `backend`; nao ha service
  para `backend/app/worker.py`.

Evidencia de log:

- Nao houve logs de `/server/api/analysis-runs/.../execute`,
  `/server/api/repositories/.../analyze`, `/server/api/github/webhooks` ou execucao
  de scanners no periodo retornado.
- O unico backend runtime observado foi `health` e `auth/me`.

Impacto:

- A API pode aceitar pedidos de analise com `202`, mas nenhum processo consome a
  fila se nao houver worker separado rodando.
- Isso pode parecer "sem erro na Vercel", porque enfileirar com sucesso nao gera
  excecao e job parado na fila nao aparece como stack trace.

Como corrigir:

1. Implantar um worker persistente para executar `python -m app.worker` ou
   `python backend/app/worker.py` com o mesmo acesso a `DATABASE_URL` e segredos
   necessarios.
2. Preferencia tecnica: mover esse worker para ambiente de container ou background
   worker dedicado, com CPU, tempo e disco suficientes para scanners. Exemplos:
   Render Background Worker, Fly, Railway, ECS, Cloud Run Jobs, ou VM pequena.
3. Manter a Vercel como frontend/API fina: rotas HTTP criam jobs e consultam status;
   o worker externo consome `analysis_jobs`.
4. Adicionar logs estruturados em `analysis_queue.enqueue`, `claim_next`,
   inicio/fim de `execute_analysis_run`, erro por gate e duracao por gate.
5. Adicionar metrica/endpoint administrativo para jobs `queued` mais antigos que N
   minutos, jobs `running` estagnados e ultima execucao do worker.

Validacao esperada apos a correcao:

- Ao clicar em Analyze, um job muda de `queued` para `running` e depois para
  `completed` ou `error`.
- Logs do worker mostram checkout, coverage/security/technical debt e publicacao.
- Logs da Vercel continuam pequenos e mostram apenas requests HTTP.

## Achado 2 - `semgrep` e scanners pesam no backend serverless

Severidade: alta.

Evidencia de build:

- Bundle Python de `423.29 MB` no production atual.
- Bundle Python de `423.32 MB` no preview mais recente.
- Vercel precisou otimizar dependencias por exceder o tamanho padrao.

Evidencia de runtime:

- Cada cold start observado criou ambiente em `/tmp/_vc_deps` e baixou
  `semgrep (65.6MiB)`.
- A instalacao de dependencias runtime adicionou aproximadamente 1.8s antes de
  responder ate mesmo `/server/health`.

Evidencia local:

- `backend/pyproject.toml` e `backend/requirements.txt` incluem `semgrep`,
  `bandit`, `detect-secrets` e `pip-audit`.
- `backend/app/services/gates/security_gate.py` executa:
  `semgrep --json --config=auto .`, `detect-secrets scan --all-files`, `bandit`
  e `pip-audit`.
- O README informa que comandos de repositorios rodam no ambiente do backend, nao
  em container isolado por execucao.

Impacto:

- Cold start mais lento.
- Artefato maior e mais fragil.
- Scanner CLI dentro de funcao HTTP aumenta risco de timeout, consumo de memoria e
  variabilidade de build.
- Um health check nao deveria precisar baixar `semgrep`.

Como corrigir:

1. Separar dependencias da API e do worker.
2. Remover scanners CLI do pacote runtime da API Vercel. A API precisa de FastAPI,
   SQLAlchemy, auth, GitHub API e schemas; scanners ficam no worker.
3. Criar um `requirements-api.txt` ou grupo de dependencias `api` sem `semgrep`,
   `bandit`, `detect-secrets` e `pip-audit`.
4. Criar um `requirements-worker.txt` ou imagem Docker de worker com os scanners
   preinstalados.
5. Configurar o deploy da Vercel para usar apenas dependencias da API.
6. No worker, instalar ferramentas de sistema e runtimes necessarios para executar
   coverage em Python, Node e Go.

Validacao esperada:

- Build log da Vercel deixa de mostrar bundle Python de 423 MB.
- `GET /server/health` nao mostra `Downloading semgrep`.
- Tempo de cold start cai e logs de scanner aparecem no worker, nao na API.

## Achado 3 - `401` em `/server/api/auth/me` e esperado, mas vira ruido de UX

Severidade: media.

Evidencia de runtime:

- `GET /server/api/auth/me 401 [info/serverless]`.

Evidencia local:

- `backend/app/api/routes_auth.py` expõe `GET /api/auth/me`.
- `backend/app/api/deps.py` chama `session_service.get_user_for_session(...)` e
  levanta `AppError(401, "authentication_required", "Authentication is required.")`
  quando nao existe cookie de sessao.
- `frontend/src/components/AuthGate.tsx` chama `getCurrentUser()` no carregamento
  inicial e faz `.catch(setError)`.
- `frontend/src/components/ErrorMessage.tsx` renderiza a mensagem da `ApiError`.

Interpretacao:

- O `401` nao indica falha de producao. Ele significa que um visitante anonimo nao
  tinha cookie `qg_session`.
- O problema e de experiencia: a tela de login pode mostrar "Authentication is
  required." como se fosse erro, quando a acao correta e apenas mostrar o botao
  de login.

Como corrigir:

1. No `AuthGate`, tratar `ApiError` com `status === 401` como estado anonimo normal:
   `setUser(null)` e `setError(null)`.
2. Manter outros erros como falha real: 5xx, falha de rede, JSON invalido.
3. Opcionalmente criar `getOptionalCurrentUser()` no cliente para encapsular essa
   regra.
4. Opcionalmente trocar o contrato do endpoint por uma rota de sessao que retorne
   `200 { user: null }`, mas isso e uma mudanca de API maior. O `401` atual e
   RESTful e aceitavel.

Validacao esperada:

- Acesso anonimo continua gerando no maximo `401 info`, mas a UI nao mostra banner
  de erro.
- Usuario autenticado ve o dashboard normalmente.

## Achado 4 - Timeout da plataforma menor que timeout da aplicacao

Severidade: media-alta se analises rodarem dentro da Vercel.

Evidencia local:

- `vercel.json` define `maxDuration: 300` para o backend.
- `backend/app/core/config.py` define `analysis_total_timeout_seconds: 900`.
- `backend/app/services/analysis_execution_service.py` usa esse budget de 900s.

Impacto:

- Se uma analise longa rodar dentro de uma funcao Vercel, a plataforma pode matar
  a execucao em 300s antes de a aplicacao registrar erro controlado de 900s.
- Scanners como Semgrep, Bandit, testes de cobertura e chamadas de IA podem exceder
  300s em repositorios reais.

Como corrigir:

1. Preferencia: mover execucao de analise para worker fora da Vercel Functions.
2. Se insistir em rodar na Vercel, alinhar `analysis_total_timeout_seconds` para
   valor menor que `maxDuration` e validar limite do plano.
3. Dividir analises em jobs menores por gate, com persistencia de progresso e retry.
4. Registrar timeout por gate, nao apenas timeout total.

Referencia Vercel consultada:

- `https://vercel.com/docs/functions/configuring-functions/duration`

## Achado 5 - Deployments antigos de producao tinham `gitDirty=1`

Severidade: media.

Evidencia:

- Quatro deployments de producao em 2026-06-29 21:18-21:28 BRT foram criados com
  metadata `gitDirty=1`.

Impacto:

- Esses deployments podem conter arquivos nao comprometidos no commit `3bd5ffa`.
- Isso dificulta reproduzir exatamente o que foi para producao.
- Os deployments mais recentes via GitHub em `main` nao mostram esse problema.

Como corrigir:

1. Usar Git integration/merge em `main` para producao, como ja ocorreu nos
   deployments mais recentes.
2. Evitar deploy manual de worktree suja.
3. Em CI, falhar se `git status --short` nao estiver vazio antes do deploy.
4. Se for necessario deploy emergencial sujo, criar commit de hotfix ou tag e
   registrar motivo.

## Achado 6 - Observabilidade ainda e fraca para diagnostico posterior

Severidade: media.

Evidencia:

- Runtime bruto em janela ampla pode nao estar disponivel por retencao do plano.
- Uma busca textual por `webhooks` em 24h estourou o tempo.
- A aplicacao quase nao emite logs estruturados proprios nos fluxos de fila/worker.

Impacto:

- Quando uma analise falhar em producao, pode nao haver evidencia suficiente na
  Vercel para reconstruir o problema.
- Sem log drain, a retencao curta dificulta investigacao retroativa.

Como corrigir:

1. Adicionar logs estruturados JSON com `analysis_run_id`, `repository_id`,
   `pr_number`, `gate`, `status`, `duration_ms`, `error_code`.
2. Nunca logar tokens, private keys, installation tokens ou conteudo de segredos.
3. Configurar log drain/observability externa se o projeto for usado de verdade.
4. Criar dashboard simples para jobs por status e idade maxima em fila.
5. Manter `request_id` ou correlacao entre request HTTP que enfileirou e job
   processado pelo worker.

Referencia Vercel consultada:

- `https://vercel.com/docs/functions/debug-slow-functions`

## Ordem recomendada de correcao

1. Colocar o worker de analise em producao e confirmar que a fila drena.
2. Separar dependencias da API e do worker para remover `semgrep` do cold start da
   Vercel.
3. Alinhar timeout: worker com budget realista; API Vercel apenas enfileira e
   consulta status.
4. Corrigir o tratamento frontend do `401` em `/api/auth/me`.
5. Adicionar logs estruturados e alerta para jobs parados.
6. Garantir deploy de producao somente a partir de commit limpo.

## Checklist de verificacao apos aplicar correcoes

- `GET /server/health` retorna 200 sem baixar `semgrep`.
- `GET /server/api/auth/me` anonimo nao mostra erro visual na tela de login.
- `POST /api/repositories/{id}/pull-requests/{number}/analyze` cria job `queued`.
- Worker consome job e registra `running`, `completed` ou `error`.
- Logs do worker mostram cada gate executado e duracao.
- Nenhum deployment novo de producao aparece com `gitDirty=1`.
- Build da Vercel nao mostra bundle Python acima de 400 MB.

## Comandos/ferramentas usadas

- Vercel connector: `get_project`, `list_deployments`, `get_deployment`,
  `get_deployment_build_logs`, `get_runtime_errors`, `get_runtime_logs`,
  `web_fetch_vercel_url`, `search_vercel_documentation`.
- Arquivos locais revisados:
  - `.vercel/project.json`
  - `vercel.json`
  - `backend/pyproject.toml`
  - `backend/requirements.txt`
  - `backend/app/api/deps.py`
  - `backend/app/api/routes_auth.py`
  - `backend/app/api/routes_repositories.py`
  - `backend/app/api/routes_analysis.py`
  - `backend/app/services/analysis_queue.py`
  - `backend/app/worker.py`
  - `backend/app/services/analysis_execution_service.py`
  - `backend/app/services/gates/security_gate.py`
  - `frontend/src/api/client.ts`
  - `frontend/src/components/AuthGate.tsx`

