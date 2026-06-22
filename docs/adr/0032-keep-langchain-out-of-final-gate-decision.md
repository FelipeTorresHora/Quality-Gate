# Keep LangChain Out Of Final Gate Decision

Accepted on 2026-06-21. The LangChain review step will produce an AI Review Snapshot with summary, score, risks, blocking rationale, and suggestions, but it will not be the source of the Analysis Run's final Gate Decision. Gate Decision remains objective: completed gate failures force `fail`, completed gate passes allow `pass`, and operational errors produce no decision.

**Consequences**

The product can use AI to make results easier to understand without allowing the model to approve a Pull Request that failed a configured policy. Code and API names should avoid "AI decision" or "LangChain decision" for this output.
