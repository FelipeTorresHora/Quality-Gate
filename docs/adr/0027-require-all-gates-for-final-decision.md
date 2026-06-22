# Require All Gates For Final Decision

Accepted on 2026-06-21. The first real Gate Execution requires Coverage Gate, Security Gate, and Technical Debt Gate to complete before producing a Gate Decision. If any required gate fails operationally, the Analysis Run ends with `Run Status = error` and no Gate Decision.

**Consequences**

`PASS` means all three quality pillars ran and passed their configured policies. Future configuration may allow disabling a gate explicitly, but missing or failed gate execution is not treated as success in the first implementation.
