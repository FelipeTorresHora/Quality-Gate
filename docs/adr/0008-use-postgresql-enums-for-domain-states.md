# Use PostgreSQL Enums for Domain States

Accepted on 2026-06-20. Stable domain states such as analysis run status, gate decision, finding category, and finding severity will use PostgreSQL enums instead of free strings. This lets the database reject invalid states and makes enum changes explicit through Alembic migrations.
