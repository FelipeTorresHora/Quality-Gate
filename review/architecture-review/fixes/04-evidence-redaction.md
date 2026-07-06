# AR-04 — Make Evidence Redaction a shared module

## Tipo

Hardening de seguranca e refatoracao de locality.

## Prioridade

Alta. O codigo ja possui redaction para command snapshots, mas outras evidencias
persistidas e enviadas para AI Review/GitHub Publication ainda podem conter secrets.

## Contexto

O produto captura Pull Request diff, changed files, scanner output, command output e
Analysis Findings. Parte desse material pode sair do backend:

- AI Review recebe `changed_files_snapshot_json` e ate 60000 caracteres de
  `diff_snapshot`.
- GitHub Publication publica o report final como comentario/status.
- UI exibe snapshots e findings.
- Command snapshots ja passam por `redact_secrets`.

## Problema

Redaction esta presa ao `runner_service`, entao o module e shallow: ele protege somente
stdout/stderr de comandos. O resto da evidencia passa por outros caminhos sem cruzar o
mesmo seam.

O system prompt do AI Review diz para nao mencionar secrets, mas isso nao e uma protecao
de dados. Se um segredo aparecer no diff, ele ainda pode ser enviado ao modelo.

## Evidencias no codigo

- `backend/app/services/runner_service.py`
  - `CommandResult.to_snapshot` aplica `redact_secrets` em stdout/stderr.
  - `_SECRET_PATTERNS` e `redact_secrets` existem dentro do runner.
- `backend/app/services/agent/prompts.py`
  - `MAX_AI_DIFF_CHARS = 60000`.
  - `build_ai_review_input` inclui `changed_files`, `diff_snapshot` e `findings`.
- `backend/app/services/report_service.py`
  - Monta report final com snapshots, blocking reasons e suggestions.
- `backend/app/services/github_publication_service.py`
  - Publica o report final no GitHub.
- `backend/tests/test_runner_secrets.py`
  - Testa redaction apenas no contexto do runner.

## Impacto

### Seguranca

- Secrets adicionados acidentalmente em um Pull Request podem ser enviados ao AI Review.
- Findings e summaries podem propagar trechos sensiveis para GitHub Publication.
- Redaction duplicada ou ausente em caminhos futuros e provavel, porque nao ha um module
  dono da politica.

### Performance

- Redaction central permite controlar tamanho e custo de payload antes de AI Review.
- Um module unico pode aplicar truncation e sanitizacao em uma passada por evidencia.

## Objetivo

Criar um deep module de Evidence Redaction usado por todos os caminhos em que evidencia
sai do backend ou e persistida para consumo posterior.

## Escopo tecnico

1. Mover redaction para module dedicado.
   - Nome sugerido: `backend/app/services/evidence_redaction_service.py`.
   - `runner_service` deve importar esse module, nao possuir a politica.

2. Redigir diffs e changed files antes de AI Review.
   - Aplicar redaction em `diff_snapshot`.
   - Aplicar redaction em `changed_files_snapshot_json[*].patch`.
   - Aplicar redaction em strings de findings, blocking reasons e suggestions quando
     usadas fora do backend.

3. Redigir report final antes de GitHub Publication.
   - `build_github_comment_body` deve garantir que o markdown publicado esta redigido.
   - Alternativamente, garantir que `final_report_markdown` ja e persistido redigido.
   - Escolher uma regra unica e testada para evitar redaction dupla inconsistente.

4. Preservar informacao util.
   - Substituir segredo por marcador estavel, por exemplo `***REDACTED***`.
   - Manter file paths, line numbers e titulos quando seguros.

5. Tornar redaction extensivel.
   - GitHub tokens: `ghs_`, `gho_`, `github_pat_`.
   - Clone credentials: `x-access-token:...@`.
   - Private key blocks.
   - OpenAI keys (`sk-...`) e outros patterns configuraveis.
   - Generic secret assignment em diffs: `SECRET=...`, `TOKEN=...`, `PASSWORD=...`.

## Fora de escopo

- Bloquear merge/publicacao com base em secret detection. Security Gate ja cobre parte
  disso.
- Remover diff persistence do banco.
- Criar DLP completo.

## Plano de implementacao sugerido

1. Criar testes primeiro.
   - Um diff com `github_pat_...` nao aparece no AI Review input.
   - Um changed file patch com private key nao aparece no AI Review input.
   - Um command snapshot continua redigido apos mover o module.
   - Um GitHub comment body nao contem token conhecido.

2. Extrair redaction.
   - Mover `_SECRET_PATTERNS` e `redact_secrets` de `runner_service.py`.
   - Adicionar funcoes orientadas por tipo:
     - `redact_text(text: str) -> str`
     - `redact_mapping(value: dict) -> dict`
     - `redact_sequence(value: list) -> list`
     - ou uma funcao recursiva segura para JSON-like.

3. Atualizar runner.
   - `CommandResult.to_snapshot` passa a usar `evidence_redaction_service.redact_text`.

4. Atualizar AI Review input.
   - `build_ai_review_input` deve montar payload e aplicar redaction antes de retornar.
   - Garantir que `diff_truncated` continua correto.

5. Atualizar GitHub Publication/report.
   - Aplicar redaction antes de publicar.
   - Decidir se a persistencia no banco deve ser redigida ou se apenas saidas externas
     devem ser redigidas.

6. Adicionar testes de regressao.
   - Cobrir paths principais: runner, AI Review, GitHub comment.

## Criterios de aceite

- `runner_service` nao define patterns de segredo diretamente.
- AI Review input nao contem tokens, private keys ou clone credentials conhecidos.
- GitHub comment body nao contem tokens, private keys ou clone credentials conhecidos.
- Tests existentes de runner secrets continuam passando.
- O marker `***REDACTED***` aparece onde o segredo foi removido.
- A redaction e aplicada de forma recursiva em dict/list JSON-like.
- O system prompt deixa de ser a unica protecao contra mencao de secrets.

## Plano de testes

Adicionar/ajustar:

- `backend/tests/test_evidence_redaction.py`
  - `test_redact_text_masks_github_tokens_private_keys_and_assignments`
  - `test_redact_json_like_redacts_nested_patch`
- `backend/tests/test_runner_secrets.py`
  - Atualizar import para o novo module.
- `backend/tests/test_agent_review_input.py` ou equivalente
  - Validar que `build_ai_review_input` redige diff e changed files.
- `backend/tests/test_github_publication.py`
  - Validar que comment body publicado esta redigido.

Comando:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests\test_runner_secrets.py tests\test_github_publication.py
```

## Riscos

- Redaction agressiva demais pode remover dados necessarios para diagnostico.
- Redaction so na saida externa ainda deixa segredo persistido no banco.
- Redaction so na persistencia pode dificultar auditoria interna.

## Decisao necessaria

Escolher uma politica:

1. **Redigir antes de persistir**: mais seguro por padrao, menos detalhe historico.
2. **Persistir bruto e redigir antes de sair**: melhor diagnostico, maior risco em caso de
   acesso indevido ao banco.
3. **Persistir bruto criptografado + redigir saidas**: mais complexo, melhor postura para
   longo prazo.

Recomendacao para MVP: redigir antes de AI Review/GitHub Publication imediatamente e abrir
decisao separada para persistence policy.

