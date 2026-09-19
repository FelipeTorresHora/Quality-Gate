# Graphify

This repository uses [Graphify](https://github.com/Graphify-Labs/graphify) for a **local, AST-derived knowledge graph** (`graphify-out/`) and optional **Graphify Cloud** PR reviews via the Graphify Labs GitHub App. Graphify is **advisory** and separate from the PR Quality Gate product (coverage, security, technical debt, and QG publish flows).

## Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) (recommended) or pipx

```bash
uv tool install graphifyy
```

The PyPI package is `graphifyy`; the CLI command is `graphify`.

## Project layout

| Path | Purpose |
| --- | --- |
| `graphify-out/graph.json` | Persistent graph (committed; shared team baseline) |
| `graphify-out/manifest.json` | Incremental extraction manifest (portable relative paths) |
| `graphify-out/GRAPH_REPORT.md` | High-level map: communities, hubs, suggested questions |
| `graphify-out/graph.html` | Interactive viewer (optional; open locally) |
| `.graphifyignore` | Extra scan exclusions (merged with `.gitignore`) |
| `.agents/skills/graphify/` | Agent Skills–compatible `/graphify` skill |
| `.cursor/rules/graphify.mdc` | Cursor always-on graph guidance |
| `AGENTS.md` | Codex / shared agent graph rules |
| `CLAUDE.md` | Includes a `## graphify` section for Claude Code |

Local-only (not committed): `graphify-out/cache/`, `graphify-out/cost.json`, `graphify-out/.graphify_*`.

## First-time setup (developer)

From the repository root:

```bash
graphify install --project --platform cursor   # or: agents, claude, codex
graphify hook install                          # post-commit AST refresh + graph.json merge driver
```

After `git pull` or merge:

```bash
graphify update .
```

Rebuild the graph manually (code-only, no API key):

```bash
graphify extract . --code-only
graphify cluster-only . --no-label
```

Query from the terminal:

```bash
graphify query "how does analysis execution enqueue work?"
graphify path "AnalysisRun" "GitHubClient"
```

See [Graphify docs](https://docs.graphify.com/) and the upstream [README](https://github.com/Graphify-Labs/graphify/blob/v8/README.md).

## CI

Workflow [`.github/workflows/graphify.yml`](../.github/workflows/graphify.yml) rebuilds the code graph on relevant changes and fails if `graphify-out/` is out of date. Update locally and commit when you change scanned code.

## Graphify Cloud and GitHub PR reviews

Hosted reviews (`graphify-labs[bot]`) use **Graphify Cloud**, not the QG application:

1. Sign in at [app.graphify.com](https://app.graphify.com).
2. **Repositories** → connect this GitHub repository (install/authorize the Graphify GitHub App when prompted).
3. Wait for indexing to reach **Indexed**; enable **PR reviews** (and optional formal verification) in the repository settings in Cloud.
4. On pull requests, the bot posts **advisory** grounded findings. Reply with `@graphify good`, `@graphify wrong`, or `@graphify suppress` per [Pull request reviews](https://docs.graphify.com/platform/reviews.md).

Do **not** add Graphify as a required GitHub status check for the Quality Gate product. QG merge visibility remains independent (see project ADRs).

## Relationship to Quality Gate

| | Graphify | PR Quality Gate (QG) |
| --- | --- | --- |
| Purpose | Code graph + advisory PR review | Coverage, security, debt gates + optional AI explanation |
| Merge blocking | Not configured here | Not required by product policy |
| GitHub identity | `graphify-labs[bot]` | QG GitHub App / `ai-quality-gate` status when published |
