# Use Manual GitHub Publication For MVP

Accepted on 2026-06-22. Superseded by [0043-auto-publish-github-as-satellite](0043-auto-publish-github-as-satellite.md).

Fase 9 published Analysis Run results to GitHub through an explicit dashboard/API action instead of automatically publishing during Gate Execution. The existing repository Quality Gate Config flags decide which channels are enabled: Pull Request comment, commit status, or both.

**Consequences**

Gate Execution stays focused on analysis and does not fail because GitHub write permissions or network calls fail after a decision is produced. Automatic publication was later added around the same publication service without changing the Analysis Run decision model.
