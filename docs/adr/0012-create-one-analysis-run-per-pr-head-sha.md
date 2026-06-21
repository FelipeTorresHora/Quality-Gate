# Create One Analysis Run per PR Head SHA

Accepted on 2026-06-21. Automatic Pull Request triggers will create at most one `AnalysisRun` for each `repository_id`, `pr_number`, and `head_sha`. Replayed webhooks and repeated events for the same commit reuse the existing run, while a new commit on the same Pull Request creates a new run.

This keeps Analysis Run history aligned with the exact Pull Request commit that was evaluated, avoids duplicate runs from GitHub delivery retries, and gives later quality gates stable snapshot evidence to process.
