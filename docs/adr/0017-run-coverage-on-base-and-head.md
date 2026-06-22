# Run Coverage On Base And Head

Accepted on 2026-06-21. Coverage Gate will calculate coverage drop by running the configured coverage command on both the Pull Request base SHA and head SHA, then comparing the parsed reports. This is slower than using a stored baseline, but it makes the first real Coverage Gate independent of dashboard history and gives each Analysis Run self-contained evidence.

**Consequences**

Gate Execution needs checkout support for both base and head revisions. Coverage Result Snapshots should include base coverage, Pull Request coverage, coverage drop, changed-files coverage when available, and enough command/report metadata to diagnose failures.
