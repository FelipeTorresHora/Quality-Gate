# Plano de correção — Análise de Pull Request

Objetivo: fazer o workflow de análise de PR funcionar em produção e fechar as falhas de
segurança graves. Os arquivos deste diretório trazem o código pronto para aplicar.

> Os relatórios HTML (`../index.html`) explicam o **porquê** de cada item. Aqui está o **como**.

## Ordem recomendada

A causa-raiz do "erro em produção" é arquitetural: o pipeline pesado roda **dentro da
requisição HTTP**, em um **runtime serverless sem o toolchain** que ele exige. Os dois
primeiros passos resolvem isso; os demais corrigem corretude e segurança.

| Ordem | Arquivo | Achados | Por quê primeiro |
|------|---------|---------|------------------|
| 1 | [03-vazamento-segredos.md](03-vazamento-segredos.md) | PA-11, PA-12, PA-13, PA-14 | **Crítico de segurança** — vazamento de `SESSION_SECRET`/`TOKEN_ENCRYPTION_KEY`. Aplicável de imediato, independente da arquitetura. |
| 2 | [01-execucao-assincrona.md](01-execucao-assincrona.md) | PA-02, PA-04 | Tira o pipeline da request. Sem isso, nada de pesado roda confiável em produção. |
| 3 | [02-runner-ambiente-e-toolchain.md](02-runner-ambiente-e-toolchain.md) | PA-01, PA-03 | Dá ao executor um ambiente com `git`/`npm`/`go`/scanners e disco gravável. |
| 4 | [04-estado-run-e-archive.md](04-estado-run-e-archive.md) | PA-05, PA-06, PA-15 | Para de prender runs em `RUNNING` e conserta download de repo privado. |
| 5 | [05-logica-cobertura.md](05-logica-cobertura.md) | PA-07, PA-08, PA-09, PA-10 | Corrige falsos positivos/negativos das regras de cobertura e débito. |

## "Quick win" para destravar produção rápido

Se o objetivo imediato é apenas **fazer a análise rodar sem 504/erro**, o menor caminho é:

1. Aplicar o `_safe_env` por allowlist (fixes/03) — segurança, não pode esperar.
2. Mover `execute_analysis_run` para fora da request com um worker durável (fixes/01).
3. Hospedar o worker num container com toolchain (fixes/02) — **não** na função serverless da Vercel.
4. Envolver o pipeline em `try/finally` e recuperar runs presos em `RUNNING` (fixes/04).

Os passos 1 e 4 são patches pequenos e isolados. Os passos 2 e 3 são a mudança estrutural
que efetivamente conserta a causa-raiz.

## Decisão de arquitetura que você precisa tomar

O serverless da Vercel **não é** um lugar adequado para clonar repositórios e rodar suítes
de teste/scanners arbitrários (sem toolchain, FS read-only, `maxDuration` curto). Escolha um:

- **(A) Worker container dedicado** (recomendado): a app web continua na Vercel/onde estiver, e
  um serviço separado (Fly.io, Railway, Render, ECS, etc.) consome uma fila e executa o
  pipeline em sandbox. Maior controle, mas você opera o sandbox.
- **(B) Delegar ao GitHub Actions**: disparar um workflow no repositório do cliente que roda
  os gates e devolve o resultado via API. O blast radius da execução de código não-confiável
  passa a ser a conta do cliente, não a sua — melhor postura de segurança (mitiga PA-12).

Os fixes 01 e 02 são escritos para a opção (A) por ser a menor mudança de código, com notas
sobre como adaptar para (B).
