# Save Partial Gate Results On Execution Error

Accepted on 2026-06-21. If one gate fails operationally while other gates produce results, Gate Execution will save the successful partial Gate Result Snapshots and any Analysis Findings, but the Analysis Run will end with `Run Status = error` and no Gate Decision. A quality decision requires all required gates to complete.

**Consequences**

Gate Execution needs per-gate error capture and a final aggregation step. The dashboard can show useful partial evidence, but must not present partial success as a passing or failing quality gate decision.
