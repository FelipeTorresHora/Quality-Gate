# PR Quality Gate Dashboard

Glossary for the product and domain language used by the PR Quality Gate Dashboard.

## Language

**MVP Tecnico de Fundacao**:
The initial build scope that establishes the web app, API, database, migrations, local Docker environment, and mock/manual workflows needed before real PR analysis exists.
_Avoid_: MVP, MVP inicial, produto final

**MVP de Produto**:
The later usable product scope where a user can connect GitHub, inspect Pull Requests, run real quality analysis, and optionally publish comments or status checks back to GitHub.
_Avoid_: Fases 0-2, fundacao

**GitHub Read-only Basico**:
The first real GitHub integration scope where the system uses a configured token to read repositories and Pull Requests without OAuth, GitHub App installation, comments, or status publication.
_Avoid_: GitHub completo, GitHub App, conexao GitHub

**Pull Request Trigger**:
A GitHub-originated Pull Request lifecycle event that tells the dashboard to start or queue an Analysis Run for a known Repository.
_Avoid_: webhook, auto analysis, automatic quality gate

**Fase 2.5**:
The milestone after the database and mock dashboard foundation that adds GitHub Read-only Basico.
_Avoid_: Fase 2, GitHub completo, MVP de Produto

**Fase 4**:
The dashboard milestone that matures the existing React screens into a cohesive user flow for repositories, Pull Requests, Quality Gate Config, mock Analysis Runs, and analysis history before real quality gates exist.
_Avoid_: real analysis, Coverage Gate, Security Gate, Technical Debt Gate

**Operational Error**:
A user-facing failure caused by configuration, permissions, external API state, or runtime conditions that should be returned with a stable code and clear message.
_Avoid_: exception, stack trace, gate failure

**Pull Request**:
A GitHub-owned change proposal that the dashboard reads and may analyze; the source of truth for its current state remains GitHub.
_Avoid_: analise, execucao, Pull Request salvo

**Analysis Run**:
A dashboard-owned record of one attempt to evaluate a Pull Request against the configured quality gate.
_Avoid_: Pull Request, check, job

**Analysis Trigger**:
The source that caused an Analysis Run to exist, such as a dashboard action, controlled mock scenario, or Pull Request Trigger.
_Avoid_: origin, event type, runner source

**Run Status**:
The operational state of an Analysis Run: `pending`, `running`, `completed`, or `error`.
_Avoid_: decision, result, approval

**Gate Decision**:
The quality gate outcome for a completed Analysis Run: `pass`, `fail`, or no value when the run has not produced a gate outcome.
_Avoid_: status, execution result

**Analysis Finding**:
A dashboard-owned issue found during an Analysis Run that can be displayed, filtered, and marked as blocking or non-blocking.
_Avoid_: raw result, report, log

**Gate Result Snapshot**:
The structured per-pillar result captured for an Analysis Run, stored as historical evidence rather than as the primary query model.
_Avoid_: finding, metric table, live scanner output

**Pull Request Snapshot**:
The historical Pull Request metadata captured for an Analysis Run so the dashboard can explain which GitHub state was analyzed.
_Avoid_: live Pull Request data, current PR state

**Pull Request Review State**:
The dashboard-owned summary shown beside a live Pull Request, derived from the latest relevant Analysis Run for that Pull Request.
_Avoid_: Pull Request status, GitHub check, live analysis

**Changed File Snapshot**:
The historical changed-file list and patch content captured for an Analysis Run as input evidence for later quality gates.
_Avoid_: file cache, stored GitHub file, repository file

**Mock Analysis Scenario**:
A controlled fake Analysis Run shape used to exercise the dashboard before real analyzers exist.
_Avoid_: real analysis, fixture, random result

**Quality Gate Config**:
The repository-owned policy that defines which coverage, security, and technical debt conditions block a Pull Request analysis.
_Avoid_: settings, preferences, scanner config

**Dashboard Summary**:
A dashboard-owned aggregate view of Repository, Analysis Run, Gate Decision, and Analysis Finding counts used as the starting point for understanding project quality activity.
_Avoid_: metrics cache, analytics warehouse, navigation page

**Repository**:
A GitHub repository identity known by the dashboard, identified initially by its `owner/name` full name.
_Avoid_: user repository, project, repo config

**GitHub Connection**:
A future user-owned GitHub credential relationship prepared for authentication and permission flows, but not used to own repositories in the foundation build.
_Avoid_: global GitHub token, repository ownership

**Local Developer**:
The seeded user identity used by the local foundation build before real authentication exists.
_Avoid_: usuario real, conta GitHub
