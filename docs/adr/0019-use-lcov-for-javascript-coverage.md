# Use LCOV For JavaScript Coverage

Accepted on 2026-06-21. TypeScript and JavaScript Coverage Gate support will initially require LCOV reports. Jest, Vitest, and nyc can commonly emit LCOV, which gives the MVP one stable report format for both JavaScript-family languages.

**Consequences**

The initial Coverage Execution Config defaults for TypeScript and JavaScript should point to an LCOV report path. Tool-specific JSON formats are out of scope until a concrete repository requires them.
