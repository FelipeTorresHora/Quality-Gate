# Store Analysis Result Snapshots as JSONB

Accepted on 2026-06-20. Coverage, security, and technical debt outputs will initially be stored on `AnalysisRun` as PostgreSQL `JSONB` snapshots, while `AnalysisFinding` holds the queryable issues. This keeps the foundation stable while analyzers are still mock or evolving, without prematurely normalizing result shapes that are likely to change.
