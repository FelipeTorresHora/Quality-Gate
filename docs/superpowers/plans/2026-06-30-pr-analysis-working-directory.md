# PR Analysis Working Directory Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix Manual Pull Request Analysis for repositories whose runnable project lives below the Git repository root.

**Architecture:** Keep Quality Gate Config as policy and extend Coverage Execution Config with one operational field, `working_directory`, defaulting to `"."`. The runner remains the module that owns command execution; gates pass the configured directory and do not duplicate path handling.

**Tech Stack:** FastAPI, SQLAlchemy 2.0, Alembic, Postgres, pytest.

---

### Task 1: Coverage Execution Config Interface

**Files:**
- Modify: `backend/app/models/coverage_execution_config.py`
- Modify: `backend/app/schemas/coverage_execution_config.py`
- Modify: `backend/app/services/coverage_execution_config_service.py`
- Modify: `backend/tests/test_coverage_execution_config.py`
- Create: `backend/alembic/versions/20260630_0008_add_coverage_working_directory.py`

- [ ] **Step 1: Write the failing test**

Add this assertion to `test_synced_repository_has_default_coverage_execution_config`:

```python
assert config["working_directory"] == "."
```

Add this test:

```python
def test_update_coverage_execution_config_accepts_working_directory(client, repository):
    response = client.put(
        f"/api/repositories/{repository['id']}/coverage-execution-config",
        headers={"X-CSRF-Token": repository["csrf_token"]},
        json={"working_directory": "docker-log-watcher-agent"},
    )

    assert response.status_code == 200
    assert response.json()["working_directory"] == "docker-log-watcher-agent"
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
cd backend
pytest tests/test_coverage_execution_config.py::test_synced_repository_has_default_coverage_execution_config tests/test_coverage_execution_config.py::test_update_coverage_execution_config_accepts_working_directory -q
```

Expected: FAIL because `working_directory` is missing from the response schema.

- [ ] **Step 3: Write minimal implementation**

Add `working_directory` to the model, schema, and update service:

```python
working_directory: Mapped[str] = mapped_column(Text, nullable=False, default=".")
```

```python
working_directory: str | None = Field(default=None, min_length=1)
```

Create an Alembic migration:

```python
op.add_column(
    "coverage_execution_configs",
    sa.Column("working_directory", sa.Text(), nullable=False, server_default="."),
)
op.alter_column("coverage_execution_configs", "working_directory", server_default=None)
```

- [ ] **Step 4: Run test to verify it passes**

Run the same pytest command. Expected: PASS.

### Task 2: Runner Executes Coverage in Configured Directory

**Files:**
- Modify: `backend/app/services/runner_service.py`
- Modify: `backend/app/services/gates/coverage_gate.py`
- Modify: `backend/tests/test_coverage_gate.py`

- [ ] **Step 1: Write the failing test**

Add a coverage-gate test with a fake workspace whose `run(command, working_directory=...)` records the directory used for install/test commands. The test must call `run_coverage_gate` with `coverage_config.working_directory == "docker-log-watcher-agent"` and assert both coverage commands used that directory.

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
cd backend
pytest tests/test_coverage_gate.py::test_coverage_gate_runs_commands_in_configured_working_directory -q
```

Expected: FAIL because `RunnerWorkspace.run` has no `working_directory` parameter and coverage does not pass one.

- [ ] **Step 3: Write minimal implementation**

Update `RunnerWorkspace.run`:

```python
def run(self, command: str, working_directory: str = ".") -> CommandResult:
    cwd = (self.repo_path / working_directory).resolve()
    if not cwd.is_relative_to(self.repo_path.resolve()):
        raise RunnerError("Working directory must stay inside the repository.")
    if not cwd.exists() or not cwd.is_dir():
        raise RunnerError(f"Working directory does not exist: {working_directory}.")
    result = run_command(command, cwd, timeout_seconds=self.command_timeout_seconds)
    self.command_metadata.append(result.to_snapshot())
    return result
```

Update `_run_revision_coverage` to pass `coverage_config.working_directory` to install and test commands and resolve the report path from that directory.

- [ ] **Step 4: Run test to verify it passes**

Run the same pytest command. Expected: PASS.

### Task 3: Manual Analysis Regression

**Files:**
- Modify: `backend/tests/test_manual_pr_analysis.py`

- [ ] **Step 1: Write the failing test**

Add a Manual Pull Request Analysis test that uses the real endpoint, real executor, and monkeypatched `RunnerWorkspace`/GitHub context to simulate a repository with coverage evidence below `docker-log-watcher-agent/`. The test should set `coverage_execution_config.working_directory = "docker-log-watcher-agent"` and assert the response status is `completed`, not `error`.

- [ ] **Step 2: Run test to verify it fails before Task 2 implementation**

Run:

```bash
cd backend
pytest tests/test_manual_pr_analysis.py::test_manual_analyze_uses_coverage_working_directory_for_nested_project -q
```

Expected before implementation: FAIL with an operational coverage error.

- [ ] **Step 3: Run test after Task 2 implementation**

Run the same pytest command. Expected: PASS with `status == "completed"`.

### Task 4: Verification and Real PR

**Files:**
- Modify only files from Tasks 1-3 unless verification reveals a missing schema/type update.

- [ ] **Step 1: Run targeted backend tests**

```bash
cd backend
pytest tests/test_coverage_execution_config.py tests/test_coverage_gate.py tests/test_manual_pr_analysis.py -q
```

- [ ] **Step 2: Run broader backend suite if Postgres is available**

```bash
cd backend
pytest -q
```

- [ ] **Step 3: Open a real GitHub PR for end-to-end analysis**

Create a small branch in a repository installed in the GitHub App, edit a harmless file under the nested project directory, push it, and open a PR. Use the production dashboard to analyze that PR and verify the Analysis Run completes rather than reporting an operational coverage error.
