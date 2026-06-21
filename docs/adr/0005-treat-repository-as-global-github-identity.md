# Treat Repository as Global GitHub Identity

Accepted on 2026-06-20. During the foundation build, `Repository.full_name` will be globally unique and represent the GitHub repository identity, not a per-user association. User-specific access and repository membership can be modeled later with a separate association when real authentication and tenancy exist.
