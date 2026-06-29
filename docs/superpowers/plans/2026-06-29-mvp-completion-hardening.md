# MVP Completion Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the remaining MVP Product gaps, verify the app, and open a new Pull Request.

**Architecture:** Keep the existing FastAPI, SQLAlchemy, React, Vite, and Docker Compose architecture. Make narrowly scoped hardening changes around deterministic configuration, runner dependencies, CSRF validation, and documentation accuracy.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic Settings, pytest, React, TypeScript, Vite, Docker Compose, GitHub CLI.

---

### Task 1: Backend Test Configuration Isolation

**Files:**
- Modify: `backend/tests/conftest.py`
- Modify: `backend/tests/test_github_app_auth.py`

- [ ] **Step 1: Add a failing regression test**

Add a test proving GitHub App JWT generation does not read `backend/.env` when the test explicitly removes private key configuration:

```python
def test_generate_app_jwt_ignores_local_env_file_when_key_unset(monkeypatch):
    monkeypatch.setenv("GITHUB_APP_ID", "123")
    monkeypatch.delenv("GITHUB_APP_PRIVATE_KEY", raising=False)
    monkeypatch.delenv("GITHUB_APP_PRIVATE_KEY_PATH", raising=False)
    github_app_auth_service.get_settings.cache_clear()

    with pytest.raises(Exception) as exc:
        github_app_auth_service.generate_app_jwt()

    assert "github_app_private_key" in str(exc.value)
```

- [ ] **Step 2: Verify red**

Run:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests\test_github_app_auth.py -v
```

Expected before the fix: the missing-key test fails because local `.env` supplies a private key path.

- [ ] **Step 3: Implement isolation**

Set `ENV_FILE` or equivalent test-only settings before importing `app.main`, so tests do not read developer `.env` files by default.

- [ ] **Step 4: Verify green**

Run the same targeted test file and then the full backend suite.

### Task 2: Runner Dependencies In Docker

**Files:**
- Modify: `backend/Dockerfile`
- Modify: `backend/requirements.txt`
- Modify: `README.md`

- [ ] **Step 1: Add missing scanner dependencies**

Ensure the backend image has `git` and Python scanner CLIs used by `security_gate.py`: `semgrep`, `detect-secrets`, `bandit`, and `pip-audit`.

- [ ] **Step 2: Keep Python dependencies precise**

Remove accidental or conflicting package additions if they are not required by the app. Keep `PyJWT` and `psycopg[binary]` as the canonical dependencies.

- [ ] **Step 3: Document runner limits**

Document that Node and Go coverage require toolchains available in the backend image or a customized runner image.

- [ ] **Step 4: Verify build path**

Run frontend build and backend tests. If possible, run Docker build/config validation without starting long-running services.

### Task 3: Secrets And Config Hygiene

**Files:**
- Modify: `.env.example`
- Modify: `README.md`

- [ ] **Step 1: Replace committed example secrets with placeholders**

Set GitHub App ID, client ID, client secret, slug, webhook secret, private key path, session secret, token encryption key, and OpenAI API key to empty placeholders.

- [ ] **Step 2: Document rotation requirement**

Add a short warning that any value copied into `.env.example`, logs, or PRs must be rotated.

- [ ] **Step 3: Verify no tracked secret-like values remain**

Search tracked files for `sk-`, `GITHUB_WEBHOOK_SECRET=`, and concrete GitHub App secrets.

### Task 4: CSRF Enforcement For Mutations

**Files:**
- Modify: `backend/app/api/deps.py`
- Modify: `backend/app/services/session_service.py`
- Modify: backend route tests as needed

- [ ] **Step 1: Add failing tests**

Add tests proving authenticated POST/PUT requests without matching `X-CSRF-Token` fail and requests with the cookie/header token pass.

- [ ] **Step 2: Implement dependency**

Create a dependency that validates the `qg_csrf` cookie and `X-CSRF-Token` header against the stored session token hash.

- [ ] **Step 3: Apply only to mutating authenticated routes**

Apply the dependency to logout, config updates, manual execution, manual analyze, and GitHub publication. Do not apply it to GitHub webhooks.

- [ ] **Step 4: Update frontend client**

Read the `qg_csrf` cookie and send `X-CSRF-Token` on non-GET API requests.

- [ ] **Step 5: Verify**

Run auth, repository, quality gate, coverage config, manual analysis, and publication tests plus frontend build.

### Task 5: Documentation Accuracy

**Files:**
- Modify: `CLAUDE.md`
- Modify: `README.md`

- [ ] **Step 1: Remove stale mock-analysis statements**

Update `CLAUDE.md` so it matches the current GitHub App/OAuth, no-mock product.

- [ ] **Step 2: Keep local setup instructions consistent**

Ensure `README.md` describes `.env.example` as a template only and documents scanner/runtime prerequisites.

### Task 6: Verification And PR

**Files:**
- No direct code files unless verification finds defects.

- [ ] **Step 1: Run verification loop**

Run:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests
cd ..\frontend
npm run build
cd ..
git diff --check
```

- [ ] **Step 2: Create branch and commit**

Create a `codex/` branch, stage only relevant files, and commit.

- [ ] **Step 3: Push and open PR**

Push the branch and open a Pull Request with the GitHub CLI.
