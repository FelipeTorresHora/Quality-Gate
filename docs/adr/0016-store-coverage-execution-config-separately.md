# Store Coverage Execution Config Separately

Accepted on 2026-06-21. Coverage Execution Config will be stored in a dedicated Repository-owned one-to-one table instead of being added to Quality Gate Config. Quality Gate Config remains the blocking policy, while Coverage Execution Config owns operational instructions such as language, test command, report path, and report format.

**Consequences**

Repository creation should create a default Coverage Execution Config alongside the default Quality Gate Config. Future Security Gate and Technical Debt Gate execution configuration can follow the same separation if needed.
