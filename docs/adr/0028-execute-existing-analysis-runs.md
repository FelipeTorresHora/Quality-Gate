# Execute Existing Analysis Runs

Accepted on 2026-06-21. Real Gate Execution will run against an existing Analysis Run identified by `analysis_run_id` instead of creating a run directly from live Pull Request inputs. The Analysis Run owns the head SHA, Pull Request Snapshot, Changed File Snapshot, and diff evidence used by the gates.

**Consequences**

The execution endpoint should be shaped around `POST /api/analysis-runs/{analysis_run_id}/execute`. If the dashboard needs to analyze a live Pull Request without a matching pending Analysis Run, it must first capture or create the Analysis Run context and then execute it.
