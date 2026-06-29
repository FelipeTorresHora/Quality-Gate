# Use One Analysis Run per Repository PR Head SHA

Accepted on 2026-06-23. Automatic Pull Request Analysis creates or reuses one `AnalysisRun` for each repository, Pull Request number, and head SHA. Repository policy is shared, so analysis evidence and results are shared by users who can access the repository instead of being duplicated per user.
