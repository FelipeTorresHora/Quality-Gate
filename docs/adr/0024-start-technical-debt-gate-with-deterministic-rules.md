# Start Technical Debt Gate With Deterministic Rules

Accepted on 2026-06-21. Fase 7 will start Technical Debt Gate with deterministic rules: new TODO/FIXME detection for all supported languages, Python function length and complexity checks, and function length checks for TypeScript, JavaScript, and Go. Deeper language-specific complexity and architecture review are deferred.

**Consequences**

Technical Debt Gate should not depend on LangChain in Fase 7. Python can use AST/Radon-backed checks, while TypeScript, JavaScript, and Go may start with simpler source parsers or conservative heuristics for function length.
