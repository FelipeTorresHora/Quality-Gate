# Fix 05 — Lógica de cobertura e débito técnico

Cobre **PA-08** (base+head dobram o custo), **PA-07** (arquivo ausente = 0%), **PA-09**
(mismatch de paths) e **PA-10** (analisador de chave ingênuo).

---

## 1. Não rodar a suíte inteira para a base por padrão (PA-08)

`run_coverage_gate` chama `_run_revision_coverage` para `base_sha` **e** `head_sha` — 2
instalações + 2 suítes por análise. A base só é necessária quando o policy de
`max_coverage_drop` está ativo.

**Arquivo:** `backend/app/services/gates/coverage_gate.py`

```python
needs_base = quality_config.max_coverage_drop is not None and \
             quality_config.max_coverage_drop >= 0
with workspace:
    head_report = _run_revision_coverage(workspace, head_sha, coverage_config)
    base_report = (
        _run_revision_coverage(workspace, base_sha, coverage_config)
        if needs_base else None
    )
base_coverage = base_report.total_coverage if base_report else head_report.total_coverage
```

E em `apply_coverage_policy`, só avalie o drop quando há base medida (quando `base_report` é
`None`, `coverage_drop = 0` e a regra de drop não dispara).

> Melhoria adicional: cachear o `total_coverage` por `(repository_id, sha)` para reaproveitar a
> medição da base entre análises do mesmo merge-base (evita recomputar).

---

## 2. Arquivo alterado sem dados de cobertura ≠ 0% (PA-07)

Distinga "arquivo não medido" de "0% coberto" e pondere por linhas.

**Arquivo:** `coverage_gate.py`, em `calculate_changed_files_coverage`:

```python
covered_lines = 0
total_lines = 0
unmatched: list[str] = []
for filename in source_files:
    coverage = normalized_report.get(_normalize_path_for_match(filename))
    if coverage is None:
        unmatched.append(filename)      # não medido — NÃO conta como 0%
        continue
    covered_lines += coverage.covered_lines      # ver nota sobre o CoverageReport
    total_lines += coverage.total_lines

if total_lines == 0:
    # nenhum arquivo alterado tinha dado de cobertura: não dá para afirmar reprovação
    return ChangedCoverageResult(changed_files_coverage=None, changed_source_files=source_files)

percentage = round(100 * covered_lines / total_lines, 2)   # ponderado por linha
```

Exponha `unmatched` no snapshot como aviso (`"warnings": ["N changed files had no coverage data"]`)
para o usuário saber que a métrica é parcial, em vez de reprovar silenciosamente.

> Se `CoverageReport.files[...]` hoje só guarda `percentage`, estenda os parsers
> (`coverage_parsers/*`) para também devolver `covered_lines`/`total_lines`. Se não for viável
> agora, ao menos pare de empurrar `0` para arquivos ausentes — ignore-os e avise.

---

## 3. Reconciliar paths GitHub × relatório (PA-09)

Paths do GitHub são relativos à raiz; os do relatório dependem de `working_directory` e da
ferramenta. Faça o match tolerante a prefixos.

**Arquivo:** `coverage_gate.py`

```python
def _normalize_path(path: str) -> str:
    return path.replace("\\", "/").removeprefix("./")   # removeprefix, não lstrip("./")

def _match_keys(path: str, working_directory: str) -> list[str]:
    norm = _normalize_path(path)
    keys = {norm}
    wd = _normalize_path(working_directory).strip("/")
    if wd and norm.startswith(wd + "/"):
        keys.add(norm[len(wd) + 1:])     # remove o prefixo do working_directory
    return list(keys)
```

No casamento, tente as chaves do arquivo alterado contra o índice do relatório, com fallback por
**sufixo** (último recurso): um arquivo do relatório casa se `report_path.endswith("/" + changed_key)`.
Documente que o match por sufixo pode colidir em nomes repetidos (`index.ts`) — por isso ele é
fallback, não a regra primária.

> A causa de `lstrip("./")` (PA, nota menor): `lstrip` remove *qualquer* `.`/`/` inicial, então
> `.github/workflows/ci.yml` → `github/workflows/ci.yml`. `removeprefix("./")` corrige isso.

---

## 4. Analisador de "função longa" de linguagens de chave (PA-10)

`analyze_brace_language_file` conta `{`/`}` em texto bruto, incluindo strings/regex/comentários,
e marca o finding como **blocking**. Duas saídas:

### Opção curta (segura agora): rebaixar de blocking para informativo

**Arquivo:** `technical_debt_gate.py`, em `analyze_brace_language_file`:

```python
GateFinding(
    category=FindingCategory.TECHNICAL_DEBT,
    severity=FindingSeverity.LOW,
    ...,
    blocking=False,   # heurística não-confiável não deve reprovar o PR
)
```

Assim a contagem de chave imprecisa deixa de **bloquear** PRs por engano, mas continua visível.

### Opção robusta: parser real

Para de fato medir tamanho/complexidade em JS/TS/Go, use `tree-sitter` (parsers por linguagem) e
conte nós de função reais, como o lado Python já faz com `ast`. Maior esforço; faça quando o
gate de débito para essas linguagens precisar voltar a ser blocking.

---

## Checklist

- [ ] Base de cobertura só quando `max_coverage_drop` ativo (PA-08); cache por SHA (opcional)
- [ ] Arquivo não medido vira `unmatched`/aviso, não 0%; média ponderada por linha (PA-07)
- [ ] Match de path tolerante a `working_directory` + `removeprefix("./")` (PA-09)
- [ ] Finding de função longa em linguagem de chave: `blocking=False` (ou parser real) (PA-10)
