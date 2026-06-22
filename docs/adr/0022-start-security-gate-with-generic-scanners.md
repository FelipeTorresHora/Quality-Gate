# Start Security Gate With Generic Scanners

Accepted on 2026-06-21. Fase 6 will start Security Gate with generic scanners across supported repositories: Semgrep and detect-secrets. Python receives additional first-pass checks with Bandit and pip-audit, while JavaScript, TypeScript, and Go dependency audit tools are deferred until concrete repository needs justify the operational variation.

**Consequences**

Security Gate should normalize findings from generic scanners into Analysis Findings. JavaScript package audit, TypeScript-specific audit behavior, and Go vulnerability tooling should be added later as explicit extensions rather than assumed by the initial multi-language coverage scope.
