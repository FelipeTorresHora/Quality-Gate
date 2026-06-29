# GitHub App OAuth Multi-User GitHub-Only Analysis Design

## Scope

Replace the current token-based, mock-capable foundation with a GitHub-connected multi-user product flow.

This design covers:

- GitHub OAuth Login using the GitHub App user authorization flow;
- HTTP-only dashboard sessions;
- GitHub App Installation tracking;
- repository access filtering per authenticated User;
- repository-shared Quality Gate Config and Coverage Execution Config;
- Repository Admin authorization for policy changes;
- Installation Token based GitHub API access, clone access, Pull Request context capture, publication, and webhooks;
- automatic real analysis for supported Pull Request webhook events;
- manual real analysis from selected live GitHub Pull Requests;
- total removal of mock analysis creation and arbitrary PR number/head SHA entry.

## Non-Goals

This scope does not add billing, organizations inside the dashboard, custom dashboard roles, SAML, SCIM, enterprise policy management, branch protection management, merge queue support, persistent job queues, Redis, per-run containers, retry/versioned reruns, or per-user quality policies.

The first implementation still executes Gate Execution in the backend process. A queue/worker architecture is the correct next step, but it is not required to make the product behavior GitHub-only.

This scope does not require a separate OAuth App. The GitHub App provides both user authorization and installation access.

## External Documentation Inputs

The design is based on GitHub's current official documentation and the `github/docs` repository inspected through the GitHub plugin.

- [Differences between GitHub Apps and OAuth apps](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/differences-between-github-apps-and-oauth-apps)
- [Generating a user access token for a GitHub App](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/generating-a-user-access-token-for-a-github-app)
- [Generating a JSON Web Token for a GitHub App](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/generating-a-json-web-token-jwt-for-a-github-app)
- [Authenticating as a GitHub App installation](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/authenticating-as-a-github-app-installation)
- [Validating webhook deliveries](https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries)
- [Permissions required for GitHub Apps](https://docs.github.com/en/rest/authentication/permissions-required-for-github-apps)
- [REST API endpoints for pull requests](https://docs.github.com/en/rest/pulls/pulls)
- [REST API endpoints for issue comments](https://docs.github.com/en/rest/issues/comments)
- [REST API endpoints for commit statuses](https://docs.github.com/en/rest/commits/statuses)
- [REST API endpoints for check runs](https://docs.github.com/en/rest/checks/runs)

Key documentation implications:

- GitHub Apps are preferred over OAuth Apps for integrations because they use fine-grained permissions, selected repository access, centralized webhooks, and short-lived installation tokens.
- A GitHub App can also generate user access tokens through the OAuth web flow; this is enough for dashboard login and user-visible repository access discovery.
- Installation access tokens expire after one hour and should be generated on demand.
- Installation tokens can be used for REST API, GraphQL API, and HTTP-based Git access when the app has the required permissions.
- Webhook deliveries must be validated with `X-Hub-Signature-256` against the raw request body using HMAC SHA-256 and constant-time comparison.
- Creating Pull Request issue comments requires either Issues write or Pull requests write repository permission.
- Creating commit statuses requires Commit statuses write repository permission.
- Listing Pull Request files requires Pull requests read repository permission.

## Product Direction

The dashboard becomes usable only after GitHub is connected.

The intended flow is:

```text
User signs in with GitHub
-> User installs or links the GitHub App
-> Dashboard syncs installed repositories
-> User sees only repositories they can access through GitHub/App intersection
-> Repository Admin configures the repository quality policy
-> GitHub App receives Pull Request events
-> Dashboard creates/reuses one Analysis Run for repository + PR + head SHA
-> Dashboard executes real Gate Execution automatically
-> Dashboard shows shared result to users with repo access
-> User may manually analyze a selected live PR only when no current run exists
```

Mock analysis is not a fallback, not a development mode in the product UI, and not a public API.

## Domain Model

`GitHub OAuth Login` identifies the User. The dashboard stores a local User and creates a local Session.

`GitHub App Installation` grants repository access to the app for a user or organization account.

`Installation Token` is the operational credential used for repository reads, Pull Request context capture, HTTP Git clone, GitHub Publication, and webhook-driven automation.

`Repository` remains a global GitHub repository identity, keyed by GitHub repository ID and `owner/name`.

`Repository Admin` is a User whose GitHub permissions allow them to administer the repository policy in the dashboard.

`Quality Gate Config` and `Coverage Execution Config` are shared per Repository. They are not per User.

`Automatic Pull Request Analysis` is created from a GitHub App Pull Request event and produces one shared Analysis Run for each repository, PR number, and head SHA.

`Manual Pull Request Analysis` is initiated by a User from a selected live GitHub Pull Request and immediately executes the real gate flow if no current run exists for that PR/head SHA.

## Authentication Architecture

Use one GitHub App registration for both user login and repository installation.

The login flow:

```text
GET /api/auth/github/login
-> create OAuth state and PKCE verifier
-> store state/verifier in short-lived auth state storage
-> redirect to https://github.com/login/oauth/authorize
-> GitHub redirects to /api/auth/github/callback?code=...&state=...
-> backend validates state
-> backend exchanges code for GitHub App user access token
-> backend calls GitHub /user
-> backend upserts User and GitHub Connection
-> backend creates local Session
-> backend sets HTTP-only session cookie
-> backend redirects to frontend
```

The dashboard session is the app's authentication mechanism. The frontend never receives a GitHub token.

Session cookie requirements:

- HTTP-only;
- `SameSite=Lax`;
- `Secure=true` outside local development;
- path `/`;
- bounded expiration;
- server-side revocation support.

CSRF protection:

- OAuth `state` protects the login callback.
- Mutating authenticated API routes should require either a CSRF header paired with a non-HTTP-only CSRF cookie or an equivalent same-origin CSRF mechanism.
- GitHub webhook routes do not use dashboard CSRF; they rely on GitHub HMAC signature verification.

## User Access Token Handling

GitHub App user access tokens are used for user identity and user-accessible installation discovery. They are not used for Gate Execution, GitHub Publication, HTTP Git clone, or webhook automation.

Persist encrypted GitHub user access token and refresh token only if needed for:

- refreshing the user's visible installations without forcing login;
- checking the intersection of user access and app installation access;
- resolving Repository Admin permissions.

Token storage rules:

- encrypt user access token and refresh token at rest;
- store token expiration timestamps;
- refresh token before use when expired and refresh token is available;
- clear/revoke stored token metadata when GitHub sends `github_app_authorization` revocation;
- never log token values;
- never pass user access tokens into runner child processes.

If token encryption is not configured, the backend should fail startup in non-development environments.

## GitHub App Installation Architecture

The installation flow:

```text
Authenticated User clicks "Install GitHub App" or "Manage GitHub Access"
-> frontend opens GitHub App installation URL
-> User selects account and repositories on GitHub
-> GitHub redirects to app setup URL with installation_id and setup_action
-> backend verifies current user session
-> backend syncs installation metadata and repositories
-> frontend returns to repository list
```

Installation webhooks must also sync installation state:

- `installation.created`: upsert installation and repositories;
- `installation.deleted`: mark installation inactive and hide repositories that have no active accessible installation;
- `installation.suspend`: mark installation suspended;
- `installation.unsuspend`: mark installation active;
- `installation_repositories.added`: add repository access;
- `installation_repositories.removed`: remove repository access.

Repository discovery should be driven primarily by installation state and user access intersection:

```text
GitHub App installation has repository A
User GitHub access includes repository A
=> user can see repository A in dashboard
```

## GitHub App Permissions

The GitHub App should request the minimum practical permissions for the target product behavior.

Required repository permissions:

- Metadata: read. Required baseline for repository metadata.
- Contents: read. Required for HTTP Git clone with installation token and reading repository contents.
- Pull requests: read. Required to list Pull Requests, read Pull Request details, and list changed files.
- Issues: write or Pull requests: write. Required to create/update Pull Request issue comments. Prefer Pull requests write if it covers the comment endpoint for the installation; otherwise use Issues write.
- Commit statuses: write. Required to create commit statuses on head SHAs.

Optional repository permissions:

- Checks: write. Defer unless switching from commit statuses to Check Runs.

Required webhook events:

- Pull request.
- Installation.
- Installation repositories.
- GitHub App authorization.

Optional webhook events:

- Check run, only if Check Runs are added later.

## Persistence Changes

### `users`

Extend the existing `users` table to become the local authenticated principal:

```text
id UUID primary key
github_user_id bigint unique not null
github_login text unique not null
name text nullable
email text nullable
avatar_url text nullable
created_at
updated_at
last_login_at
```

Email may be null because GitHub users can hide email. Do not use email as the only stable identity key.

### `user_sessions`

Add server-side session persistence:

```text
id UUID primary key
user_id UUID not null references users(id)
session_token_hash text unique not null
csrf_token_hash text nullable
expires_at timestamptz not null
revoked_at timestamptz nullable
last_seen_at timestamptz nullable
created_at
updated_at
```

Only a random session token is stored in the browser cookie. The database stores a hash.

### `github_connections`

Replace the current placeholder token model with GitHub App user authorization metadata:

```text
id UUID primary key
user_id UUID not null references users(id)
github_user_id bigint not null
github_login text not null
access_token_encrypted text nullable
refresh_token_encrypted text nullable
access_token_expires_at timestamptz nullable
refresh_token_expires_at timestamptz nullable
revoked_at timestamptz nullable
created_at
updated_at
```

The token fields are only for user identity/access discovery. Operational repository access uses installation tokens.

### `github_app_installations`

Add installation tracking:

```text
id UUID primary key
installation_id bigint unique not null
account_id bigint not null
account_login text not null
account_type text not null
repository_selection text nullable
permissions_json jsonb not null default '{}'
events_json jsonb not null default '[]'
active boolean not null default true
suspended_at timestamptz nullable
created_at
updated_at
```

`installation_id` is the key needed to generate installation tokens.

### `installation_repositories`

Connect active installations to global repositories:

```text
id UUID primary key
installation_id UUID not null references github_app_installations(id)
repository_id UUID not null references repositories(id)
github_repo_id bigint not null
full_name text not null
created_at
updated_at
unique(installation_id, repository_id)
```

`repositories` remains globally unique by GitHub repo ID/full name.

### `user_repository_access`

Cache the current user's accessible repositories and admin status:

```text
id UUID primary key
user_id UUID not null references users(id)
repository_id UUID not null references repositories(id)
installation_id UUID not null references github_app_installations(id)
permission text nullable
is_admin boolean not null default false
synced_at timestamptz not null
created_at
updated_at
unique(user_id, repository_id)
```

`is_admin` should be derived from GitHub permission data, not assigned manually in the dashboard.

### `repositories`

Keep `Repository` global. Continue to store:

```text
github_repo_id
owner
name
full_name
default_branch
```

Do not add `user_id` to `repositories`.

### `quality_gate_configs`

Keep one config per Repository:

```text
repository_id unique
...
```

Policy write routes require `Repository Admin`.

### `coverage_execution_configs`

Keep one config per Repository:

```text
repository_id unique
...
```

Execution config write routes require `Repository Admin`.

### `analysis_runs`

Keep the existing uniqueness rule:

```text
unique(repository_id, pr_number, head_sha)
```

Update `trigger_source` values to remove product use of mock:

```text
github_webhook
manual
```

If the PostgreSQL enum currently includes `mock`, the migration deletes existing mock Analysis Runs and dependent findings, then rebuilds the enum without `mock`. Because the requested removal is total and the project is still in local MVP shape, preserving mock history is not required.

## Backend API Surface

### Auth

```http
GET /api/auth/me
GET /api/auth/github/login
GET /api/auth/github/callback
POST /api/auth/logout
```

`GET /api/auth/me` returns:

```json
{
  "id": "uuid",
  "github_user_id": 123,
  "github_login": "octocat",
  "name": "Octo Cat",
  "avatar_url": "https://...",
  "has_github_connection": true
}
```

Unauthenticated API routes return:

```json
{
  "detail": {
    "code": "authentication_required",
    "message": "Authentication is required."
  }
}
```

### GitHub App Installation

```http
GET /api/github/installations
POST /api/github/installations/sync
GET /api/github/installations/callback
```

The sync endpoint refreshes installation/repository access for the current User using the GitHub App user access token and installation metadata.

### Repositories

```http
GET /api/repositories
GET /api/repositories/{repository_id}
```

Repository creation from arbitrary owner/name is removed from the authenticated product flow. Repositories enter the dashboard by GitHub App installation sync or installation webhook.

The existing manual creation endpoint should be removed or made internal-only for tests. It must not be available in product UI.

All repository reads require the current User to have `user_repository_access`.

### Pull Requests

```http
GET /api/repositories/{repository_id}/pull-requests
GET /api/repositories/{repository_id}/pull-requests/{pr_number}/context
POST /api/repositories/{repository_id}/pull-requests/{pr_number}/analyze
```

All Pull Request GitHub API calls use an Installation Token for the repository's active installation.

Manual analyze behavior:

```text
validate user can access repository
fetch live Pull Request context through installation token
if current Analysis Run exists for repository + pr_number + head_sha:
    return existing run without re-executing
else:
    create Analysis Run with trigger_source=manual
    execute Gate Execution immediately
    return AnalysisRunDetail
```

### Quality Gate Config

```http
GET /api/repositories/{repository_id}/quality-gate-config
PUT /api/repositories/{repository_id}/quality-gate-config
```

Read requires repository access. Update requires Repository Admin.

### Coverage Execution Config

```http
GET /api/repositories/{repository_id}/coverage-execution-config
PUT /api/repositories/{repository_id}/coverage-execution-config
```

Read requires repository access. Update requires Repository Admin.

### Analysis Runs

```http
GET /api/repositories/{repository_id}/analysis-runs
GET /api/analysis-runs/{analysis_run_id}
POST /api/analysis-runs/{analysis_run_id}/publish-github
```

Listing/detail requires repository access.

Publishing should require Repository Admin in this scope because it writes back to GitHub under repository policy.

The existing public execute endpoint can remain only for already-created pending runs, but the normal product path no longer exposes a generic Execute button. If retained, it must require repository access and should reject runs that are not pending.

### Removed API

Remove:

```http
POST /api/repositories/{repository_id}/analysis-runs/mock
POST /api/repositories
POST /api/repositories/github
```

If repository creation endpoints are kept temporarily for tests, move them behind test-only fixtures and do not expose them in the frontend client.

## GitHub Client Architecture

Split the current `GitHubClient` responsibilities.

```text
app/services/github_app_auth_service.py
  generate_app_jwt()
  generate_installation_token(installation_id)
  refresh_user_access_token(connection)

app/services/github_oauth_service.py
  build_authorization_url()
  exchange_code_for_user_token()
  get_authenticated_user()

app/services/github_installation_service.py
  sync_installation()
  sync_user_repository_access()
  get_installation_for_repository()
  require_repository_access()
  require_repository_admin()

app/services/github_client.py
  low-level REST calls using provided token
```

The low-level client should not know where the token came from. Application services decide whether a route requires user access token or installation token.

Installation token caching:

- cache token in memory by installation ID until close to expiration;
- never persist installation tokens to the database;
- regenerate token on 401 caused by expiration;
- never log token values.

HTTP Git clone:

- clone private repositories with the Installation Token;
- avoid embedding token in persisted command metadata;
- if using token in a command string, store a redacted command snapshot;
- prefer a runner API that separates `actual_command` from `display_command`;
- do not pass GitHub, OpenAI, LangSmith, database, or session secrets into repository test commands.

## Webhook Processing

The webhook endpoint remains:

```http
POST /api/github/webhooks
```

Required validation:

- read raw request body;
- require `X-Hub-Signature-256`;
- compute HMAC SHA-256 with `GITHUB_WEBHOOK_SECRET`;
- compare with constant-time comparison;
- reject invalid signatures before parsing payload.

Supported events:

- `pull_request`;
- `installation`;
- `installation_repositories`;
- `github_app_authorization`.

Pull Request actions:

```text
opened
reopened
synchronize
ready_for_review
```

Ignored Pull Request cases:

- closed PR;
- unsupported action;
- draft PR except `ready_for_review`;
- repository not included in an active installation;
- installation suspended.

Automatic Pull Request Analysis:

```text
validate webhook signature
read installation.id and repository.id from payload
upsert/sync repository and installation metadata
fetch full Pull Request context using installation token
create/reuse Analysis Run for repository + pr_number + head_sha
if newly created and pending:
    execute Gate Execution automatically
return GitHubWebhookResult
```

Idempotency:

- duplicate webhook deliveries must not create duplicate Analysis Runs;
- if the existing run is completed/error/running for the same head SHA, return it and do not re-execute;
- if the existing run is pending, execute it once.

Initial execution implementation:

- product behavior is automatic analysis;
- webhook-created analysis uses FastAPI `BackgroundTasks` so GitHub receives a fast acknowledgement without adding Redis/workers;
- manual analysis remains request/response synchronous and returns the final `AnalysisRunDetail`;
- tests must prove a new PR event schedules execution and that manual analysis executes immediately.

## Gate Execution Changes

Gate Execution must stop assuming public GitHub clone URLs.

Update runner workspace creation to accept repository clone credentials:

```text
repository full_name
installation_id
installation token provider
```

Coverage Gate, Security Gate, and Technical Debt Gate continue to operate on checked-out files. They should not know about OAuth or sessions.

Analysis Execution Service responsibilities:

- load Analysis Run with Repository, Quality Gate Config, Coverage Execution Config, and active installation;
- obtain Installation Token;
- create runner workspace with authenticated clone;
- run gates;
- persist snapshots, findings, AI Review Snapshot, and final report;
- apply objective Gate Decision;
- optionally publish to GitHub if future auto-publication is enabled by config.

Manual and automatic flows should both call the same execution service. The only difference is `trigger_source`.

## GitHub Publication

Publication uses Installation Token.

Existing behavior remains:

- create/update marked Pull Request issue comment when enabled;
- create commit status on `head_sha` when enabled;
- map pass/fail/error to success/failure/error.

Permission requirements:

- Pull Request comment: Issues write or Pull requests write.
- Commit status: Commit statuses write.

Publication must not use a user's OAuth token. GitHub activity is attributed to the GitHub App installation.

Manual publication requires Repository Admin. Automatic publication can be added later as a separate policy decision.

## Frontend Changes

### App Shell

Unauthenticated users see a GitHub login entry point, not the repository dashboard.

Authenticated users see:

- current GitHub identity;
- repository list from GitHub App installation access;
- install/manage GitHub App action;
- logout action.

### Repository List

Remove manual repository creation.

Repository list states:

- no GitHub login: login required;
- logged in but no installations: show install GitHub App action;
- installations synced but no repositories: show manage installation action;
- repositories available: list accessible repositories.

### Pull Request List

Remove:

- Mock Analysis Controls;
- scenario selector;
- manual PR number input;
- manual head SHA input;
- Create Mock Analysis button.

For each live PR:

- show latest review state for current head SHA;
- show Analyze button only when no current run exists;
- if current run is pending due to race/older flow, show Analyze/Execute current run;
- if current run is running, show running state;
- if current run is completed/error, show View detail;
- if current run is outdated, show previous run and allow Analyze current head.

### Config Screens

Read access is allowed for users with repository access.

Inputs are editable only for Repository Admin. Non-admin users see read-only config and a clear disabled state.

### Analysis Detail

Require access to the underlying repository.

Publish to GitHub button is visible only to Repository Admin and only when publication is enabled by config.

## Removing Mock Analysis

Remove backend:

- `SCENARIOS`;
- `MockAnalysisRunCreate`;
- `create_mock_analysis_run`;
- mock route;
- mock trigger creation paths;
- mock-specific tests as product tests.

Remove frontend:

- `MockScenario` type;
- `createMockAnalysisRun` client method;
- Mock Analysis Controls panel;
- Create Mock Analysis buttons;
- empty states that tell users to create mock runs.

Remove documentation:

- README references that describe mock scenarios as product capability;
- validation checklist items for mock creation;
- old terms that suggest mock analysis is supported.

Migration:

- delete local/dev mock Analysis Runs and dependent findings before removing enum support, or explicitly mark a one-time local data reset as required.
- Because this project is still in local MVP shape, deleting mock rows is acceptable for the requested total removal.

## Error Handling

Use stable `AppError` codes.

Authentication:

- `authentication_required`;
- `session_expired`;
- `csrf_token_invalid`;
- `github_oauth_state_invalid`;
- `github_oauth_exchange_failed`.

Authorization:

- `repository_access_denied`;
- `repository_admin_required`;
- `github_installation_required`;
- `github_installation_suspended`.

GitHub App:

- `github_app_config_missing`;
- `github_app_jwt_failed`;
- `github_installation_token_failed`;
- `github_user_token_refresh_failed`;
- `github_rate_limited`;
- `github_permission_denied`.

Manual analysis:

- `pull_request_not_found`;
- `analysis_run_already_current`;
- `analysis_run_not_pending`.

Webhook:

- `github_webhook_secret_missing`;
- `github_webhook_signature_invalid`;
- `github_webhook_payload_invalid`.

Operational gate failures remain Operational Errors and must not become quality failures.

## Configuration

Add environment variables:

```text
GITHUB_APP_ID
GITHUB_APP_CLIENT_ID
GITHUB_APP_CLIENT_SECRET
GITHUB_APP_PRIVATE_KEY
GITHUB_APP_PRIVATE_KEY_PATH
GITHUB_APP_SLUG
GITHUB_WEBHOOK_SECRET
GITHUB_API_VERSION
SESSION_SECRET
SESSION_COOKIE_NAME
SESSION_COOKIE_SECURE
TOKEN_ENCRYPTION_KEY
AUTH_CALLBACK_URL
FRONTEND_ORIGIN
```

Notes:

- support either `GITHUB_APP_PRIVATE_KEY` or `GITHUB_APP_PRIVATE_KEY_PATH`;
- keep `GITHUB_WEBHOOK_SECRET`, but reinterpret it as the GitHub App webhook secret;
- remove `GITHUB_TOKEN` from normal product configuration;
- `GITHUB_API_VERSION` should be explicit. If the implementation keeps the existing `2022-11-28` version, document that version pinning is intentional; upgrading API versions is separate work.

## Security Requirements

- No GitHub token is exposed to frontend JavaScript.
- No token is stored in command metadata, logs, final reports, gate snapshots, or Analysis Findings.
- Session token is stored hashed in the database.
- User access and refresh tokens are encrypted at rest.
- Installation tokens are not persisted.
- Webhook payloads are validated before parsing business fields.
- Repository commands receive a stripped environment without app secrets.
- Authenticated mutating API calls use CSRF protection.
- Repository policy updates require Repository Admin.
- Repository result reads require repository access.

## Testing

Backend tests should cover:

- OAuth login URL includes `client_id`, `state`, callback, and PKCE values;
- callback rejects missing/invalid state;
- callback exchanges code, validates GitHub user identity, upserts User, creates Session, and sets HTTP-only cookie;
- `/api/auth/me` returns current user for valid session;
- logout revokes session;
- expired/revoked session is rejected;
- installation callback syncs installation and repositories;
- installation webhook created/deleted/suspended updates installation state;
- installation repositories webhook adds/removes repository access;
- repository list is filtered by current user access;
- non-admin cannot update Quality Gate Config;
- Repository Admin can update Quality Gate Config;
- non-admin cannot update Coverage Execution Config;
- Repository Admin can update Coverage Execution Config;
- Pull Request list uses Installation Token;
- manual analyze fetches live PR context and executes when no current run exists;
- manual analyze returns existing current run without rerun;
- pull_request webhook validates signature before processing;
- supported PR webhook creates/reuses run and triggers execution;
- duplicate PR webhook is idempotent;
- draft/closed/unsupported PR webhook is ignored;
- webhook for suspended installation is ignored;
- installation token generation signs JWT with RS256 and calls the installation access token endpoint;
- installation token is not persisted;
- Git clone command metadata redacts installation token;
- GitHub Publication uses Installation Token;
- mock route no longer exists;
- mock scenario creation service no longer exists;
- existing mock rows are removed or unsupported by migration.

Frontend tests or build verification should cover:

- unauthenticated app shows GitHub login;
- authenticated app shows current GitHub identity;
- repository list has no manual create form;
- no mock controls render anywhere;
- PR row shows Analyze only when no current run exists;
- PR row shows View detail for completed/current run;
- config forms are read-only for non-admin users;
- config forms are editable for Repository Admin;
- TypeScript build passes.

Integration smoke tests should cover:

```text
GitHub OAuth callback -> session -> installation sync -> repository visible
repository admin edits config -> live PR manual analyze -> completed/error run
pull_request webhook opened -> automatic analysis started/executed
completed run -> publish comment/status using installation token
```

## Success Criteria

This scope is complete when:

1. users can sign in with GitHub through the GitHub App OAuth web flow;
2. the dashboard uses HTTP-only server-side sessions;
3. repositories enter the product through GitHub App installation sync/webhooks;
4. users only see repositories they can access through the GitHub/user/app intersection;
5. Repository Admin is required for quality policy and coverage execution changes;
6. Quality Gate Config and Coverage Execution Config remain shared per Repository;
7. all GitHub repository operations use Installation Tokens;
8. private repository clone works with Installation Token without leaking tokens into metadata;
9. supported Pull Request webhooks create/reuse one Analysis Run per repository/PR/head SHA;
10. new webhook-created runs execute automatically;
11. selected live PRs can be manually analyzed when no current run exists;
12. current runs are not rerun in place;
13. mock analysis creation is removed from backend, frontend, docs, and tests;
14. GitHub Publication uses Installation Tokens;
15. backend tests and frontend TypeScript build pass.

## Related Decisions

- `docs/adr/0003-separate-run-status-from-gate-decision.md`
- `docs/adr/0005-treat-repository-as-global-github-identity.md`
- `docs/adr/0006-keep-identity-scaffolding-uncoupled-from-repositories.md`
- `docs/adr/0035-require-repository-admin-for-policy-changes.md`
- `docs/adr/0036-use-one-analysis-run-per-repository-pr-head-sha.md`
- `docs/adr/0037-manual-analysis-only-for-live-github-pull-requests.md`
- `docs/adr/0038-execute-pr-webhook-analysis-automatically.md`
- `docs/adr/0039-use-http-only-session-cookies.md`
- `docs/adr/0040-use-installation-tokens-for-repository-access.md`
- `docs/adr/0041-remove-mock-analysis-from-product.md`
