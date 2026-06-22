# Add Install Command To Coverage Execution Config

Accepted on 2026-06-21. Coverage Execution Config will include an optional install command in addition to the test command, report path, and report format. Because Coverage Gate compares base and head revisions, the install command should run after checking out each revision so dependency changes in the Pull Request are reflected in the evidence.

**Consequences**

Coverage execution may be slower, but it is more accurate for Pull Requests that change dependencies. The command runner must apply the same timeout, environment restrictions, and workspace handling to install commands and test commands.
