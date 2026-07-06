# AR-02 — Batch Pull Request Review State

## Tipo

Melhoria de performance e refatoracao de query.

## Prioridade

Alta para repositorios com muitos Pull Requests abertos. Media para uso pequeno/local.

## Contexto

A tela de Pull Requests busca os Pull Requests abertos no GitHub e mostra, para cada um,
um Pull Request Review State derivado do Analysis Run mais recente daquele PR. A rota
limita a lista do GitHub a 50 Pull Requests, mas o review state e calculado um por vez.

## Problema

`github_service.list_repository_pull_requests` chama
`pull_request_review_service.get_pull_request_review_state` dentro de uma list
comprehension. Esse module de review state tem uma interface shallow: recebe um unico PR
e executa uma query para aquele PR. O caller, porem, naturalmente possui a lista inteira.

Resultado: a tela pode gerar 1 chamada ao GitHub + N queries ao banco, onde N e a
quantidade de Pull Requests retornados.

## Evidencias no codigo

- `backend/app/services/github_service.py`
  - `list_pull_requests` usa `per_page=50`.
  - `list_repository_pull_requests` monta a resposta chamando review state por PR.
- `backend/app/services/pull_request_review_service.py`
  - `get_pull_request_review_state` executa uma query por `repository_id` e `pr_number`.
- `backend/app/api/routes_repositories.py`
  - `list_pull_requests` cacheia o payload por repository, mas o miss ainda paga o custo
    N+1.
- `backend/tests/test_repositories.py`
  - Cobre os estados `not_run`, `current` e `outdated` para um PR, mas nao cobre
    eficiencia para lista.

## Impacto

### Performance

- A latencia cresce linearmente com o numero de Pull Requests.
- O banco recebe queries pequenas e repetidas, com overhead maior que uma consulta
  agrupada.
- Cache miss em Pull Request list fica caro; a TTL atual e curta (`30s`), entao a dor
  reaparece com frequencia.

### Seguranca operacional

- Uso ineficiente de banco aumenta superficie de DoS acidental por usuarios autenticados.
- Um repositorio com muitos PRs pode degradar a experiencia de outros usuarios se o banco
  for pequeno.

## Objetivo

Deepen o module de Pull Request Review State para calcular o estado de uma lista de Pull
Requests com uma unica consulta ao banco, preservando o comportamento atual.

## Escopo tecnico

1. Adicionar uma operacao batch no module de review state.
   - Entrada conceitual: `repository_id` + lista de Pull Requests.
   - Saida conceitual: mapa por `pr_number` ou lista ja enriquecida.
   - Nao expor detalhes de query ao `github_service`.

2. Buscar latest Analysis Run por PR em uma query.
   - Deve retornar no maximo um Analysis Run por `pr_number`.
   - Deve ordenar por `created_at desc, id desc`, preservando a semantica atual.
   - Deve limitar aos `pr_number` presentes na lista vinda do GitHub.

3. Preservar semantica atual.
   - Sem run: `state="not_run"`.
   - Head SHA igual ao Pull Request: `state="current"`.
   - Head SHA diferente: `state="outdated"`.

4. Evitar regressao de autorizacao.
   - A rota deve continuar chamando `require_repository_access` antes de ler cache ou
     consultar GitHub/banco.

## Fora de escopo

- Paginar todos os Pull Requests alem dos 50 atuais.
- Alterar cache TTL.
- Alterar contrato da API publica.
- Alterar frontend.

## Plano de implementacao sugerido

1. Escrever teste de eficiencia.
   - Inserir 3 Analysis Runs para PRs diferentes.
   - Mockar `GitHubClient.list_pull_requests` para retornar 3 PRs.
   - Instrumentar queries ou monkeypatchar a funcao antiga para garantir que o fluxo nao
     chama `get_pull_request_review_state` por item.

2. Criar helper batch.
   - Nome sugerido: `get_pull_request_review_states(db, repository_id, pull_requests)`.
   - Internamente, montar `pr_numbers = [pr.number for pr in pull_requests]`.

3. Implementar query.
   - Opcao Postgres: usar window function `row_number() over (partition by pr_number
     order by created_at desc, id desc)`.
   - Opcao SQLAlchemy simples: buscar todos os runs dos PRs relevantes ordenados e montar
     o primeiro por PR em Python. Para ate 50 PRs isso e suficiente e mais simples.

4. Atualizar `github_service.list_repository_pull_requests`.
   - O module deve pedir o mapa/lista batch uma vez.
   - A montagem de `GitHubPullRequestWithReviewState` deve consumir o resultado batch.

5. Manter a funcao single-item.
   - Pode continuar existindo para compatibilidade interna ou ser implementada em cima do
     batch com lista de um item.

## Criterios de aceite

- `list_repository_pull_requests` faz uma consulta de latest runs para todos os PRs.
- A resposta da API nao muda.
- Estados `not_run`, `current` e `outdated` continuam iguais.
- Cache hit continua exigindo `require_repository_access` antes de retornar dados.
- Teste novo cobre multiplos PRs e evita retorno incorreto quando existem varios runs para
  o mesmo PR.

## Plano de testes

Adicionar/ajustar:

- `backend/tests/test_repositories.py`
  - `test_list_pull_requests_batches_review_state_for_multiple_prs`
  - `test_list_pull_requests_uses_latest_run_per_pr`
  - `test_list_pull_requests_keeps_not_run_for_pr_without_run`
- Possivel teste unitario novo:
  - `backend/tests/test_pull_request_review_service.py`

Comando:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests\test_repositories.py
```

## Riscos

- Query batch pode escolher um run errado se a ordenacao nao replicar a query atual.
- Carregar todos os runs historicos dos PRs pode crescer caso um PR tenha muitas analises.

## Mitigacoes

- Manter ordenacao `created_at desc, id desc`.
- Usar window function se o volume historico por PR crescer.
- Testar com dois runs no mesmo PR e head SHA diferente.

