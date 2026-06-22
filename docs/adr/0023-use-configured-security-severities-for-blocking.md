# Use Configured Security Severities For Blocking

Accepted on 2026-06-21. Security Gate will normalize scanner output into `low`, `medium`, `high`, and `critical` severities, then mark findings as blocking when their severity is included in `Quality Gate Config.security_fail_on`. The default remains `critical` and `high`.

**Consequences**

Fase 6 does not require AI judgment to decide whether a scanner finding blocks an Analysis Run. Security scanner adapters must map tool-specific severities into the domain severity set before persistence.
