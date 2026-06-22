# Use Manual GitHub Publication For MVP

Accepted on 2026-06-22. Fase 9 will publish Analysis Run results to GitHub through an explicit dashboard/API action instead of automatically publishing during Gate Execution. The existing repository Quality Gate Config flags decide which channels are enabled: Pull Request comment, commit status, or both.

**Consequences**

Gate Execution stays focused on analysis and does not fail because GitHub write permissions or network calls fail after a decision is produced. Automatic publication can be added later around the same publication service without changing the Analysis Run decision model.
