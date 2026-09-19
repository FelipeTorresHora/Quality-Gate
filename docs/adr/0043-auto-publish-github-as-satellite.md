# Auto-Publish GitHub as Satellite

Accepted on 2026-09-19. Gate Execution publishes to GitHub automatically after an Analysis Run is marked `running` (commit status `pending`) and again after `completed` or `error` (comment plus `success` / `failure` / `error` status). Publication reuses the existing GitHub publication service and Statuses API context `ai-quality-gate`, with `target_url` pointing at the Analysis Run in the dashboard.

This supersedes [0034-use-manual-github-publication-for-mvp](0034-use-manual-github-publication-for-mvp.md) for the default product path. The dashboard Publish action remains as republish. New repositories default `comment_on_github` and `publish_github_status` to true; existing repositories are not bulk-migrated.

**Consequences**

A GitHub write failure is logged and returned as a publication result; it must not change Run Status or Gate Decision. The product does not create Check Runs, required status checks, or branch protection, and it does not block merge.
