# Separate Run Status from Gate Decision

Accepted on 2026-06-20. `AnalysisRun.status` will represent only operational state (`pending`, `running`, `completed`, `error`), while `AnalysisRun.decision` will represent the quality gate outcome (`pass`, `fail`, or null). Failed quality gates are completed runs with `decision = fail`; technical failures use `status = error` plus an explicit `error_message`.
