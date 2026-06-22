# Use Explicit Coverage Execution Config

Accepted on 2026-06-21. Coverage execution will be configured explicitly per Repository, with language-specific defaults for Python, TypeScript, JavaScript, and Go, instead of relying only on automatic repository detection. This makes the first multi-language Coverage Gate more predictable across package managers, test commands, report paths, and monorepo layouts.

**Consequences**

Quality Gate Config remains the policy that decides whether coverage blocks an Analysis Run. Coverage Execution Config describes how to produce coverage evidence, including language, test command, report path, and report format.
