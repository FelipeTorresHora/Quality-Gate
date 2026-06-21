# Keep Identity Scaffolding Uncoupled from Repositories

Accepted on 2026-06-20. `User` and `GitHubConnection` may exist as preparation for future authentication, but `Repository` will not carry a `user_id` in the foundation build. Until real tenancy exists, repositories represent global GitHub identities and credential ownership stays separate from repository identity.
