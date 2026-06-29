# PR Quality Gate Dashboard

Glossary for the product and domain language used by the PR Quality Gate Dashboard.

## Language

**MVP Tecnico de Fundacao**:
The initial build scope that established the web app, API, database, migrations, and local Docker environment before GitHub-connected Pull Request analysis became the only supported product path.
_Avoid_: MVP, MVP inicial, produto final

**MVP de Produto**:
The later usable product scope where a user can connect GitHub, inspect Pull Requests, run real quality analysis, and optionally publish comments or status checks back to GitHub.
_Avoid_: Fases 0-2, fundacao

**GitHub Read-only Basico**:
The first real GitHub integration scope where the system uses a configured token to read repositories and Pull Requests without OAuth, GitHub App installation, comments, or status publication.
_Avoid_: GitHub completo, GitHub App, conexao GitHub

**GitHub Publication**:
The dashboard-owned action of publishing an Analysis Run result back to GitHub as a Pull Request comment, commit status, or both.
_Avoid_: write-back, GitHub sync, status job

**Pull Request Trigger**:
A GitHub-originated Pull Request lifecycle event that tells the dashboard to start or queue an Analysis Run for a known Repository.
_Avoid_: webhook, auto analysis, automatic quality gate

**Automatic Pull Request Analysis**:
The dashboard-owned creation and execution of one Analysis Run for a GitHub App Pull Request event on a repository/head SHA.
_Avoid_: per-user analysis, mock analysis, background check

**Manual Pull Request Analysis**:
The user-requested creation and immediate execution of an Analysis Run for a selected live GitHub Pull Request when no current run exists for its head SHA.
_Avoid_: mock analysis, arbitrary PR number, rerun

**Fase 2.5**:
The milestone after the database and dashboard foundation that adds GitHub Read-only Basico.
_Avoid_: Fase 2, GitHub completo, MVP de Produto

**Fase 4**:
The dashboard milestone that matured the React screens into a cohesive user flow for repositories, Pull Requests, Quality Gate Config, and analysis history before real quality gates existed.
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
The source that caused an Analysis Run to exist, such as Manual Pull Request Analysis or a Pull Request Trigger.
_Avoid_: origin, event type, runner source

**Gate Execution**:
The act of evaluating an Analysis Run against the repository's Quality Gate Config to produce Gate Result Snapshots and Analysis Findings.
_Avoid_: auto analysis, webhook analysis, mock analysis

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

**AI Review Snapshot**:
The structured interpretation produced by the LangChain review step for a completed Gate Execution, used for summary, score, risks, and suggestions without owning the final Gate Decision.
_Avoid_: AI decision, LangChain decision, final decision

**Pull Request Snapshot**:
The historical Pull Request metadata captured for an Analysis Run so the dashboard can explain which GitHub state was analyzed.
_Avoid_: live Pull Request data, current PR state

**Pull Request Review State**:
The dashboard-owned summary shown beside a live Pull Request, derived from the latest relevant Analysis Run for that Pull Request.
_Avoid_: Pull Request status, GitHub check, live analysis

**Changed File Snapshot**:
The historical changed-file list and patch content captured for an Analysis Run as input evidence for later quality gates.
_Avoid_: file cache, stored GitHub file, repository file

**Quality Gate Config**:
The repository-owned policy that defines which coverage, security, and technical debt conditions block Pull Request analysis for that repository.
_Avoid_: user preference, scanner config

**Coverage Execution Config**:
The repository-owned instructions that describe how coverage evidence should be produced before the repository's coverage policy is applied.
_Avoid_: Quality Gate Config, automatic language detection, scanner config

**Dashboard Summary**:
A dashboard-owned aggregate view of Repository, Analysis Run, Gate Decision, and Analysis Finding counts used as the starting point for understanding project quality activity.
_Avoid_: metrics cache, analytics warehouse, navigation page

**Repository**:
A GitHub repository identity known by the dashboard, identified initially by its `owner/name` full name.
_Avoid_: user repository, project, repo config

**Repository Admin**:
A User whose GitHub permissions allow them to administer the repository's dashboard-owned quality policy and execution configuration.
_Avoid_: repository owner, PR author, installer

**GitHub OAuth Login**:
The user authentication flow where a person signs in to the dashboard with their GitHub identity.
_Avoid_: GitHub repository access, installation, repository authorization

**GitHub App Installation**:
The GitHub-owned installation grant that defines which repositories the dashboard may analyze and receive events for.
_Avoid_: OAuth login, user session, global GitHub token

**Installation Token**:
A short-lived GitHub App token generated on demand to read repositories, analyze Pull Requests, and publish results for an installed repository.
_Avoid_: OAuth token, stored access token, user session token

**GitHub Connection**:
The dashboard-owned relationship between a User and their GitHub identity plus installation access state.
_Avoid_: global GitHub token, repository ownership

**Local Developer**:
The seeded user identity used by the local foundation build before real authentication exists.
_Avoid_: usuario real, conta GitHub
