# Use JSONB for Flexible Gate Policy Fields

Accepted on 2026-06-20. Quality gate policy fields such as blocking security severities will start simple but are expected to grow into richer per-repository policies. We will store flexible policy fragments in PostgreSQL `JSONB` rather than an array column or prematurely normalized tables so the foundation can support future rule shapes without an early schema redesign.
