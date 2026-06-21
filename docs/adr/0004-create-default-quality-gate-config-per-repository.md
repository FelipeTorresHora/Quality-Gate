# Create Default Quality Gate Config per Repository

Accepted on 2026-06-20. Each `Repository` will have exactly one `QualityGateConfig` in the foundation build, created with defaults when the repository is created. This keeps the API and UI from handling a missing policy state before policy inheritance or versioning exists.
