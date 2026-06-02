# Deployment Guide

## Local development

```bash
# 1. Copy environment templates
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local

# 2. Edit secrets
# - backend/.env: set JWT_SECRET, OPENAI_API_KEY (optional, for copilot)

# 3. Bring up the stack (PostGIS, Redis, backend, worker, frontend)
docker compose up --build
```

The backend container runs `alembic upgrade head` before starting Uvicorn,
so the schema is created automatically on first boot. The Celery worker
shares the same image and codebase.

- Frontend: http://localhost:3000
- API:      http://localhost:8000/docs

## Database migrations

Migrations live in `backend/alembic/versions/`. To create a new migration
after changing a model:

```bash
cd backend
alembic revision --autogenerate -m "describe the change"
# Review the generated file in alembic/versions/ before committing
alembic upgrade head
```

`compare_type=True` is set in `alembic/env.py` so column-type changes are
detected.

## Production notes

- Run `alembic upgrade head` as a separate deploy step or in the backend
  startup script. Do not rely on `Base.metadata.create_all` — it is not used.
- Use a managed PostgreSQL with PostGIS, managed Redis, and a managed object
  store. The current provider abstraction in
  `app/services/geospatial_service.py` is a deterministic mock; replace
  `SentinelNasaMockProvider` with a real Sentinel/NASA adapter for production.
- Set a strong `JWT_SECRET` and rotate via the standard JWT rotation policy.
- Restrict CORS via `CORS_ORIGINS` (comma-separated list of allowed origins).
- The Celery worker can scale horizontally; tasks are idempotent and
  Redis-backed.
- Enable observability (Prometheus, Grafana, structured logs, request IDs)
  at the reverse-proxy layer.
