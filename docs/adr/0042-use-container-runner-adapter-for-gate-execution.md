# Use Container Runner Adapter For Gate Execution

Accepted on 2026-07-06. Gate Execution now uses a runner seam with a local adapter for controlled development and tests, and an isolated container adapter for production repository command execution.

ADR-0030 allowed the MVP to run gate commands in the backend environment with temporary workspaces, timeouts, cleanup, and restricted environment variables. That remains useful for local development, but it is no longer the production default.

**Decision**

Production defaults to `RUNNER_ADAPTER=isolated` when no runner adapter is explicitly configured. The local adapter is blocked in production unless `ALLOW_LOCAL_RUNNER_IN_PRODUCTION=true` is set intentionally.

The isolated adapter runs each repository command in an ephemeral Docker container from `RUNNER_CONTAINER_IMAGE`, with:

- a bind-mounted per-run repository workspace at `/workspace`;
- non-root user `65532:65532`;
- safe environment allowlist only;
- command timeout;
- CPU, memory, PID, and `/tmp` limits;
- `RUNNER_NETWORK=none` by default.

`RUNNER_NETWORK=bridge` is available for controlled environments that must install dependencies at runtime. Allowing internet access keeps supply-chain and egress risk, so production should prefer prebuilt runner images with dependencies baked in.

**Consequences**

Gate code depends on the runner seam instead of creating subprocesses directly. Command snapshots continue to redact output and now include runner adapter and resource-limit metadata.

The first isolated adapter uses Docker on the worker host. Deployments must provide Docker access and build/publish the runner image. Stronger managed sandboxes can replace this adapter later without changing gate callers.

