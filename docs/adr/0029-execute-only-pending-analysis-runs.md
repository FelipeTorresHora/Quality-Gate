# Execute Only Pending Analysis Runs

Accepted on 2026-06-21. The real Gate Execution endpoint will execute only Analysis Runs with `Run Status = pending`. Completed, errored, and already-running Analysis Runs cannot be re-executed in place.

**Consequences**

Analysis Runs remain historical evidence of a single attempt. Retry semantics, if needed later, should be modeled explicitly rather than mutating an existing completed or errored run.
