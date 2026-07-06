# AR-01 — Deepen Gate Execution evidence workspace

## Tipo

Refatoracao arquitetural com impacto direto em performance e seguranca.

## Prioridade

Alta. Este e o primeiro ticket recomendado porque reduz trabalho repetido em cada
Analysis Run e concentra o seam de execucao de comandos, que hoje e o maior ponto de
risco do produto.

## Contexto

Gate Execution executa Coverage Gate, Security Gate, Technical Debt Gate e AI Review
para produzir Gate Result Snapshots, Analysis Findings e Gate Decision. Hoje cada gate
interage diretamente com `RunnerWorkspace` para preparar o repositorio:

- Coverage Gate baixa/extrai o archive do head e, quando `max_coverage_drop` esta ativo,
  baixa/extrai tambem o base.
- Security Gate baixa/extrai o head novamente.
- Technical Debt Gate baixa/extrai o head novamente.

Na pratica, um unico Analysis Run pode fazer quatro preparacoes de workspace para o
mesmo Pull Request: head, base, head, head. Isso espalha conhecimento de checkout,
working directory, timeout, metadata de comando, cleanup e redaction por varios modules.

## Problema

O module de Gate Execution e shallow: a interface entre `analysis_execution_service` e
os gates parece simples, mas os gates precisam saber demais sobre preparacao de
repositorio e execucao. A implementation de workspace nao tem locality suficiente,
porque cada gate decide quando fazer checkout e como consumir os artefatos.

Isso reduz depth:

- A interface dos gates inclui detalhes operacionais que deveriam ficar atras de um
  module de evidencia.
- O mesmo comportamento de checkout e command metadata precisa ser entendido em varios
  arquivos.
- Qualquer hardening futuro de timeout, cache de archive, redaction, resource limits ou
  isolamento precisa tocar varios gates.

## Evidencias no codigo

- `backend/app/services/analysis_execution_service.py`
  - Chama `coverage_gate.run_coverage_gate`, `security_gate.run_security_gate` e
    `technical_debt_gate.run_technical_debt_gate` sequencialmente.
  - Persiste snapshots parciais entre gates, mas nao possui um module comum de evidencia.
- `backend/app/services/gates/coverage_gate.py`
  - Cria `RunnerWorkspace` e chama `_run_revision_coverage` para head e base.
  - `_run_revision_coverage` chama `workspace.checkout(revision)` e roda comandos.
- `backend/app/services/gates/security_gate.py`
  - Cria outro `RunnerWorkspace`, faz checkout do head e executa scanners.
- `backend/app/services/gates/technical_debt_gate.py`
  - Cria outro `RunnerWorkspace`, faz checkout do head e le arquivos alterados.
- `backend/app/services/runner_service.py`
  - `RunnerWorkspace` concentra download/extracao/run/cleanup, mas sua interface ainda e
    consumida diretamente pelos gates, o que limita leverage.

## Impacto

### Performance

- Downloads repetidos do archive do GitHub aumentam latencia e uso de rede.
- A extracao repetida do mesmo repositorio aumenta I/O em disco e tempo total.
- Scanners e leitura de arquivos aguardam preparacoes que poderiam ser reaproveitadas.
- O timeout total de Analysis Run e consumido por trabalho duplicado.

### Seguranca

- A execucao de comandos e a redaction de output continuam distribuidas por varios
  caminhos.
- O hardening do runner fica mais dificil porque cada gate conhece detalhes do workspace.
- Um futuro sandbox adapter teria que ser encaixado em varios gates em vez de um seam
  unico.

## Objetivo

Criar um deep module de evidencia de Gate Execution que prepara e gerencia os artefatos
necessarios para todos os gates de um Analysis Run. O module deve esconder checkout,
download, extracao, command metadata, cleanup e reuso de workspace atras de uma interface
menor.

Nao desenhar uma interface publica final neste ticket. A implementacao deve escolher a
menor interface que preserve o comportamento atual e aumente locality.

## Escopo tecnico

1. Criar um module de evidencia para Gate Execution.
   - Nome sugerido: `analysis_evidence_workspace.py` ou equivalente.
   - Deve viver perto de `runner_service.py` ou dentro de um subpacote de execution, nao
     dentro de um gate especifico.

2. Centralizar preparacao de revisions.
   - Preparar head uma vez por Analysis Run.
   - Preparar base apenas quando a politica de cobertura precisar de comparacao.
   - Reaproveitar head para Security Gate e Technical Debt Gate.

3. Manter command metadata acumulada por gate.
   - Coverage snapshot ainda deve conter comandos de coverage.
   - Security snapshot ainda deve conter scanners executados e erros.
   - Technical Debt snapshot deve manter erros de leitura/checkout.
   - O module de evidencia pode expor metadata filtrada por fase, desde que os snapshots
     nao percam informacao.

4. Preservar cleanup.
   - `keep_workdir=False` deve remover os diretorios temporarios ao final.
   - `keep_workdir=True` deve manter material suficiente para debug local.

5. Preservar validacoes de path.
   - Working directory deve continuar preso dentro do repositorio.
   - `report_path` deve ser resolvido dentro da revision correta.

6. Ajustar gates para consumir evidencia preparada.
   - Coverage Gate deve pedir execucao de coverage em base/head ao module de evidencia.
   - Security Gate deve usar o workspace head preparado.
   - Technical Debt Gate deve ler arquivos do workspace head preparado.

## Fora de escopo

- Trocar o runner para container/sandbox. Isso e tratado em `06-runner-sandbox-seam.md`.
- Alterar a semantica da Gate Decision.
- Alterar a politica de coverage, security ou technical debt.
- Mudar a UI.

## Plano de implementacao sugerido

1. Adicionar testes que demonstrem a duplicacao atual.
   - Criar um fake de workspace que conta checkouts/downloads.
   - Executar um Analysis Run com todos os gates ativos.
   - O teste inicial deve falhar mostrando que head e preparado mais de uma vez.

2. Introduzir o novo module de evidencia.
   - Ele deve receber `analysis_run`, `repository`, `repository_token`,
     `coverage_config` e settings relevantes.
   - Ele deve gerenciar revisions preparadas em um cache interno por SHA.
   - Ele deve delegar download/extracao ao `RunnerWorkspace` atual para evitar reescrever
     seguranca de tarball neste ticket.

3. Migrar Coverage Gate.
   - Manter `calculate_changed_files_coverage` e `apply_coverage_policy` como pure
     implementation dentro do gate.
   - Remover do gate a responsabilidade de criar `RunnerWorkspace`.

4. Migrar Security Gate.
   - Remover criacao direta de `RunnerWorkspace`.
   - Executar scanner no head preparado.

5. Migrar Technical Debt Gate.
   - Remover criacao direta de `RunnerWorkspace`.
   - Ler changed files no head preparado.

6. Revisar snapshots.
   - Garantir que `commands` e mensagens de erro permanecem redigidos.
   - Garantir que erros parciais continuam sendo persistidos conforme ADR-0026.

7. Remover duplicacao residual.
   - Checar se apenas o module de evidencia conhece `repository_clone_url` durante Gate
     Execution.
   - Gates nao devem conhecer token de clone diretamente.

## Criterios de aceite

- Um Analysis Run com todos os gates ativos prepara head uma unica vez.
- Base so e preparada quando `max_coverage_drop` exige comparacao.
- Coverage Gate, Security Gate e Technical Debt Gate nao criam `RunnerWorkspace`
  diretamente.
- Snapshots continuam incluindo informacao de comando suficiente para diagnostico.
- Operational Error continua sem Gate Decision, conforme ADR-0018.
- Resultados parciais continuam persistidos quando um gate falha, conforme ADR-0026.
- Testes existentes de coverage, security, technical debt e analysis execution continuam
  passando.
- Novo teste cobre reuso de head entre gates.

## Plano de testes

- `backend/tests/test_analysis_execution.py`
  - Caso com todos os gates ativos e fake workspace compartilhado.
  - Caso com Security Gate falhando depois de Coverage Gate para validar snapshot parcial.
- `backend/tests/test_coverage_gate.py`
  - Cobertura de base/head preservada.
  - Working directory ainda respeitado.
- `backend/tests/test_security_gate.py`
  - Scanners executados sobre head preparado.
- `backend/tests/test_technical_debt_gate.py`
  - Leitura de arquivo alterado usa head preparado.
- `backend/tests/test_runner_archive.py`
  - Validacoes de archive continuam no `RunnerWorkspace`.

Comandos:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests\test_analysis_execution.py tests\test_coverage_gate.py tests\test_security_gate.py tests\test_technical_debt_gate.py tests\test_runner_archive.py
```

## Riscos

- Reusar workspace incorretamente pode misturar base/head e produzir cobertura errada.
- Command metadata agregada demais pode dificultar diagnostico por gate.
- Cleanup centralizado pode apagar arquivo antes de um gate terminar.

## Mitigacoes

- Tratar cada revision preparada como path imutavel.
- Nomear explicitamente head/base nos snapshots.
- Manter testes que validem report path em working directory aninhado.
- Preservar `RunnerWorkspace` como adapter interno ate o novo seam estar estavel.

