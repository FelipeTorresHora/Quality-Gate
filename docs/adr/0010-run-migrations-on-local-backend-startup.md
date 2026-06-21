# Run Migrations on Local Backend Startup

Accepted on 2026-06-20. In the Docker Compose development environment, the backend container will run `alembic upgrade head` before starting FastAPI so `docker compose up --build` creates the schema automatically. Production deployment can later separate migrations into an explicit release step.
