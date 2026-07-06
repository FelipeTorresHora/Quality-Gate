# AR-05 — Deepen GitHub OAuth Login session invariants

## Tipo

Hardening de autenticacao e configuracao.

## Prioridade

Media-alta. O fluxo atual tem boas protecoes basicas, mas as invariantes de sessao estao
espalhadas e alguns defaults sao perigosos fora de desenvolvimento.

## Contexto

GitHub OAuth Login cria uma sessao local em cookie HTTP-only, com CSRF token separado.
ADR-0039 aceita esse modelo. O produto tambem criptografa OAuth token com Fernet e usa
Installation Token para acesso a repositorios, conforme ADR-0040.

O problema nao e a direcao da arquitetura; e a distribuicao das regras de seguranca.

## Problema

As invariantes de sessao e OAuth estao espalhadas:

- `session_service` gera JWT stateless e valida CSRF claim.
- `routes_auth` define cookie policy diretamente.
- `github_oauth_service` guarda `AUTH_STATES` em memoria, sem TTL persistido.
- `config.py` possui default de `session_secret`.
- `docker-compose.yml` usa `SESSION_SECRET: ${SESSION_SECRET:-change-me}`.
- `revoke_session` e no-op.

Isso torna o module de GitHub OAuth Login shallow: a interface parece simples, mas callers
e operadores precisam saber detalhes de cookie, state, secret strength, revocation e
ambiente.

## Evidencias no codigo

- `backend/app/core/config.py`
  - `session_secret` tem default de desenvolvimento.
- `docker-compose.yml`
  - `SESSION_SECRET` defaulta para `change-me`.
- `backend/app/services/github_oauth_service.py`
  - `AUTH_STATES: dict[str, str] = {}` em memoria.
  - State e removido no callback, mas nao tem TTL/limpeza.
- `backend/app/services/session_service.py`
  - JWT stateless.
  - `revoke_session` nao revoga.
- `backend/app/api/routes_auth.py`
  - Cookie attributes sao definidos diretamente na rota.

## Impacto

### Seguranca

- Default fraco de `SESSION_SECRET` permite falsificacao de sessao se usado fora de dev.
- OAuth state em memoria quebra em multiplas replicas e nao expira de forma controlada.
- Logout nao revoga JWT ate o `exp`; so apaga cookie no browser atual.
- Cookie policy pode divergir se novos endpoints criarem cookies.

### Operacao

- Deploy com config insegura pode subir sem falhar.
- Multi-instance/backend autoscaling pode invalidar logins em andamento porque o state fica
  no processo que iniciou o login.

## Objetivo

Deepen o module de GitHub OAuth Login para que state lifecycle, session lifecycle, cookie
policy e production config guard fiquem atras de um seam unico.

## Escopo tecnico

1. Criar validation de configuracao para producao.
   - Em `APP_ENV=production`, exigir `SESSION_SECRET` forte e diferente de defaults.
   - Exigir `SESSION_COOKIE_SECURE=true` quando frontend/backend estiverem em HTTPS.
   - Exigir `TOKEN_ENCRYPTION_KEY` quando OAuth tokens forem persistidos.

2. Centralizar cookie policy.
   - Criar helper no module de sessao para set/delete dos cookies.
   - `routes_auth` nao deve codificar `httponly`, `secure`, `samesite`, `path` em varios
     lugares.

3. Persistir OAuth state com TTL.
   - Opcoes:
     - Tabela `oauth_states` no Postgres.
     - Runtime cache com TTL, se disponibilidade for suficiente.
   - Validar e consumir state atomicamente.
   - Limpar state expirado.

4. Decidir revocation.
   - Opcao simples: manter JWT stateless e documentar que logout e client-side ate exp.
   - Opcao recomendada: armazenar `jti`/hash de sessao e invalidar no logout.
   - Se usar store, `get_user_for_session` deve checar revocation/validade no store.

5. Manter CSRF atual.
   - Preservar double-submit com hash dentro da sessao ou migrar para store, mas manter
     testes de rejeicao.

## Fora de escopo

- Trocar GitHub OAuth por outro provider.
- Alterar permissoes do GitHub App.
- Implementar refresh token lifecycle completo.
- Mudar frontend alem do necessario para login/logout.

## Plano de implementacao sugerido

1. Adicionar config guard.
   - Criar funcao `validate_runtime_security_settings(settings)`.
   - Chamar na inicializacao do app ou em dependency de startup.
   - Testar `APP_ENV=production` com default fraco.

2. Extrair cookie policy.
   - Criar funcoes como `set_session_cookies(response, created_session)` e
     `clear_session_cookies(response)`.
   - Atualizar `routes_auth.github_callback` e `logout`.

3. Criar OAuth state store.
   - Model `OAuthState` ou usar runtime cache.
   - Campos se for banco: `state_hash`, `verifier_hash` se usado, `created_at`,
     `expires_at`, `consumed_at`.
   - Atualmente `verifier` e criado mas nao usado como PKCE; decidir remover ou completar
     PKCE em ticket separado.

4. Atualizar `build_login_url`.
   - Salvar state no store com TTL.
   - Nao depender de dict global.

5. Atualizar `exchange_code_for_user`.
   - Consumir state no store.
   - Rejeitar state expirado/consumido/inexistente.

6. Implementar revocation se escolhido.
   - Adicionar `jti` ao JWT.
   - Persistir hash de `jti` ou session token.
   - `revoke_session` marca revogado.
   - `get_user_for_session` valida store.

## Criterios de aceite

- Em producao, app falha cedo com `SESSION_SECRET=change-me` ou default conhecido.
- `AUTH_STATES` global deixa de existir ou fica restrito a dev/test explicitamente.
- OAuth state tem TTL e consumo atomico.
- Cookie policy e definida em um unico module.
- Logout revoga sessao se a decisao de revocation for implementada.
- Testes atuais de CSRF continuam passando.
- Login funciona em ambiente com multiplas replicas quando state store e compartilhado.

## Plano de testes

Adicionar/ajustar:

- `backend/tests/test_auth.py`
  - `test_production_rejects_default_session_secret`
  - `test_oauth_state_expires`
  - `test_oauth_state_is_single_use`
  - `test_logout_revokes_session_when_store_enabled`
  - `test_cookie_policy_helper_sets_secure_flags`
- `backend/tests/test_github_oauth_service.py` se criado.

Comando:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests\test_auth.py
```

## Riscos

- Revocation store aumenta query por request autenticada.
- OAuth state em Runtime Cache pode ser inconsistente se cache indisponivel.
- Falhar cedo por config pode quebrar ambiente local mal configurado.

## Mitigacoes

- Ativar guards estritos apenas em `APP_ENV=production`.
- Cachear validacao de sessao se necessario, com TTL curto.
- Manter fallback local somente para desenvolvimento.
- Documentar valores obrigatorios em `.env.example` e README.

