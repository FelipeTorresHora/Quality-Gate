# Treat Gate Execution Failures As Operational Errors

Accepted on 2026-06-21. Gate Execution failures such as clone errors, checkout errors, command failures, missing reports, parse failures, and timeouts will set Run Status to `error` with no Gate Decision. Quality rule violations still complete the Analysis Run and produce `Gate Decision = fail`.

**Consequences**

Gate implementation must distinguish operational failures from quality findings. Operational failures should expose stable user-facing error messages and must not create a misleading failed quality gate outcome.
