# Support Multi-Language Coverage Gate

Accepted on 2026-06-21. Fase 5 will implement Coverage Gate support for Python, TypeScript, JavaScript, and Go instead of starting as Python-only. This increases the first real gate scope, but keeps the product aligned with common Pull Request stacks by normalizing language-specific coverage outputs into the existing Gate Result Snapshot and Analysis Finding model.

**Consequences**

Coverage execution should be organized around language-specific adapters that return a shared coverage result shape. Security Gate and Technical Debt Gate do not automatically inherit this multi-language scope unless explicitly decided later.
