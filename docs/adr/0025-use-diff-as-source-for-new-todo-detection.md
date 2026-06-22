# Use Diff As Source For New TODO Detection

Accepted on 2026-06-21. Technical Debt Gate will detect new TODO/FIXME markers from the Pull Request diff or changed-file patches rather than scanning only the final checked-out files. Existing TODO/FIXME markers should not block an Analysis Run unless the Pull Request adds them.

**Consequences**

Gate Execution requires Pull Request context evidence before running Technical Debt Gate. If diff evidence is missing, new TODO/FIXME detection should be treated as unavailable instead of guessing from the final file state.
