# Run Gates In Backend Environment For MVP

Accepted on 2026-06-21. Fase 5-7 Gate Execution will run commands in the backend/local service environment with a temporary workspace, command timeout, workspace cleanup, and restricted command environment instead of creating an isolated container per Analysis Run. Per-run containers are safer, but they add Docker orchestration, volume, network, resource limit, and image management work that is out of scope for the first real gate implementation.

**Consequences**

Running untrusted Pull Request code remains a known MVP risk. Gate Execution must avoid passing application secrets into repository commands, use per-run workspaces, enforce timeouts, and document that stronger isolation is a later hardening phase.
