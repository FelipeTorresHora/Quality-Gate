# Use UUID Primary Keys

Accepted on 2026-06-20. Core entities will use UUID primary keys from the foundation build. This avoids exposing sequential identifiers in APIs and keeps the model ready for future asynchronous workers, GitHub integrations, and distributed workflows without a later primary key migration.
