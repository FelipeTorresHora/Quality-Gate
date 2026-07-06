# AR-06 — Make Runner Sandbox a real seam

## Tipo

Hardening estrutural de seguranca. Este ticket pode exigir decisao arquitetural e
infraestrutura adicional.

## Prioridade

Media-alta. O risco e alto, mas ADR-0030 documenta que executar gates no ambiente do
backend foi uma escolha consciente de MVP. A correcao completa deve ser planejada para
nao atrasar correcoes menores e imediatas.

## Contexto

ADR-0030 aceita rodar Gate Execution no ambiente do backend para o MVP, com workspace
temporario, timeout, cleanup e ambiente restrito. O codigo atual ja melhorou esse ponto
com allowlist de env e redaction de command output.

Ainda assim, Coverage Execution Config permite comandos configuraveis por repository, e
esses comandos rodam com `subprocess.run(..., shell=True)` no ambiente do backend/worker.
Isso e execucao de codigo potencialmente nao confiavel.

## Problema

`RunnerWorkspace` e um seam importante, mas hoje tem apenas um adapter real: execucao
local no processo/ambiente do backend. Pela regra de depth, um seam com um adapter ainda e
hipotetico. Como todos os gates dependem dele, a falta de um adapter isolado limita a
seguranca do produto inteiro.

## Evidencias no codigo

- `docs/adr/0030-run-gates-in-backend-environment-for-mvp.md`
  - Reconhece que containers por run seriam mais seguros, mas fora do escopo inicial.
- `backend/app/services/runner_service.py`
  - `run_command` usa `subprocess.run` com `shell=True`.
  - `_safe_env` usa allowlist, mas isso nao isola filesystem, rede, CPU ou processo.
- `backend/app/schemas/coverage_execution_config.py`
  - `install_command` e `test_command` sao configuraveis por Repository Admin.
- `backend/Dockerfile`
  - Backend image instala toolchains e scanners no mesmo ambiente.
- `docker-compose.yml`
  - Backend e worker compartilham env e volume de codigo no desenvolvimento.

## Impacto

### Seguranca

- Codigo do Pull Request pode executar comandos arbitrarios dentro do runner atual.
- Sem isolamento forte, um comando malicioso pode tentar acessar rede interna, metadata
  endpoints, disco local, processos vizinhos ou toolchain instalado.
- Allowlist de env reduz vazamento de secrets, mas nao limita o blast radius da execucao.

### Performance e disponibilidade

- Sem resource limits por run, um comando pode consumir CPU/memoria/disco e degradar o
  worker.
- Sem adapter isolado, e dificil aplicar limites diferentes por linguagem ou repository.

## Objetivo

Transformar o runner em um seam real com pelo menos dois adapters:

- adapter local para desenvolvimento e testes;
- adapter isolado para Gate Execution de repositorios reais.

O adapter isolado deve limitar filesystem, rede, processo, CPU, memoria, disco e tempo.

## Escopo tecnico

1. Definir runner port interno.
   - O restante da codebase nao deve depender de `subprocess.run` diretamente.
   - Gate Execution deve usar o seam de runner.

2. Manter adapter local.
   - Usado em testes e desenvolvimento local controlado.
   - Deve preservar comportamento atual para facilitar migracao.

3. Criar adapter isolado.
   - Opcoes:
     - container efemero por Analysis Run;
     - sandbox gerenciado;
     - delegacao para GitHub Actions.
   - A escolha deve ser registrada em ADR se mudar a decisao de ADR-0030.

4. Definir resource limits.
   - CPU.
   - Memoria.
   - PIDs.
   - Disco/tmp.
   - Timeout por comando e timeout total.

5. Definir politica de rede.
   - Bloquear metadata endpoints, especialmente `169.254.169.254`.
   - Decidir se comandos podem acessar internet para instalar dependencias.
   - Se internet for permitida, registrar o risco e aplicar egress policy quando possivel.

6. Definir filesystem.
   - Workspace por run.
   - Usuario nao-root.
   - Sem montar segredos da aplicacao.
   - Montar repo de forma controlada.

## Fora de escopo

- Corrigir redaction de AI Review. Isso esta em `04-evidence-redaction.md`.
- Corrigir reuso de workspace entre gates. Isso esta em
  `01-gate-execution-evidence-workspace.md`.
- Trocar todos os scanners.
- Criar UI de configuracao de sandbox.

## Plano de implementacao sugerido

1. Escrever ADR.
   - Reabrir ADR-0030 ou criar novo ADR.
   - Escolher entre container por run, sandbox gerenciado ou GitHub Actions.
   - Registrar tradeoffs de custo, latencia, isolamento e operacao.

2. Extrair runner port.
   - Definir dataclasses comuns para request/result de comando.
   - Garantir que command snapshot e redaction continuam iguais.
   - Manter `RunnerWorkspace` como adapter local inicial.

3. Implementar adapter isolado minimo.
   - Para container:
     - imagem runner separada do backend;
     - usuario nao-root;
     - limites de CPU/memoria/PIDs;
     - workspace temporario;
     - rede controlada;
     - timeout hard.
   - Para GitHub Actions:
     - worker dispara workflow;
     - endpoint recebe resultado assinado;
     - Analysis Run consome resultado normalizado.

4. Adicionar feature flag.
   - `RUNNER_ADAPTER=local|isolated`.
   - Em producao, bloquear `local` ou exigir override explicito.

5. Migrar Gate Execution.
   - Depois de AR-01, o module de evidencia deve usar o runner port.
   - Evitar que gates conhecam qual adapter esta em uso.

6. Adicionar observabilidade.
   - Registrar adapter usado.
   - Registrar limites aplicados.
   - Registrar timeout/resource termination de forma redigida.

## Criterios de aceite

- Gate Execution nao chama `subprocess.run` diretamente fora do adapter local.
- Existe adapter local e adapter isolado, mesmo que o isolado comece com escopo minimo.
- Producao nao usa adapter local por default.
- Repositorio analisado nao recebe secrets da aplicacao.
- Comando que excede timeout/resource limit termina como Operational Error.
- Snapshots continuam redigidos.
- ADR nova ou revisada documenta a decisao.

## Plano de testes

Adicionar/ajustar:

- `backend/tests/test_runner_protocol.py`
  - Adapter local e isolado satisfazem o mesmo contrato interno.
- `backend/tests/test_runner_secrets.py`
  - Adapter isolado nao recebe env secreto.
- `backend/tests/test_analysis_execution.py`
  - Timeout/resource failure vira `Run Status = error` sem Gate Decision.
- Teste de integracao opcional:
  - comando tenta ler env secreto e falha/nao encontra.
  - comando tenta escrever fora do workspace e falha.

Comando local para subset:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests\test_runner_protocol.py tests\test_runner_secrets.py tests\test_analysis_execution.py
```

## Riscos

- Container por run aumenta complexidade operacional.
- Bloquear internet pode quebrar `npm ci`, `pip install`, `go mod download`.
- Permitir internet mantem parte do risco de supply chain/egress.
- GitHub Actions muda ownership do tempo de execucao e exige fluxo de retorno assinado.

## Mitigacoes

- Fazer rollout por feature flag.
- Comecar com repositorios confiaveis em adapter local apenas em dev.
- Cachear dependencias em imagem/volume controlado quando possivel.
- Registrar limites por linguagem e permitir ajustes por repository apenas para admins.
- Se usar GitHub Actions, assinar resultados e validar repository/head_sha antes de aceitar.

