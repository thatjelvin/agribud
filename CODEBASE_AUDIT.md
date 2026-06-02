# Codebase Audit Report - Agribud

The repo is `agribud/agribud/` (nested twice). The project is actually branded **AgriPulse AI**. It is a FastAPI + Next.js + Celery + PostGIS monorepo with a `ml/` package. **Critical finding:** the backend is in a half-migrated state - two parallel module trees exist, and the frontend contracts do not match the active backend.

---

## Tech Stack

**Backend (Python 3.12)**
- FastAPI 0.115.5, Uvicorn 0.32.1
- SQLAlchemy 2.0.36 (async) + asyncpg 0.30, GeoAlchemy2 0.15.2
- Pydantic 2.10.2, pydantic-settings 2.6.1, email-validator
- python-jose (JWT, HS256), passlib[bcrypt]
- Celery 5.4 + redis 5.2, slowapi (rate limit)
- httpx 0.27.2, boto3 1.35.81, openai 1.58.1 (used as Groq client)
- scikit-learn 1.5.2, numpy 2.1.3 (declared but unused)
- pytest 8.3.3
- PostgreSQL 16 + PostGIS 3.4 (docker), Redis 7
- python-multipart

**Frontend (Next.js 16.2.6 / React 19.2.4 - see `frontend/AGENTS.md`: breaking changes from prior versions)**
- TypeScript 5, Tailwind CSS 4, ESLint 9
- @tanstack/react-query 5, axios 1.16
- leaflet 1.9 + react-leaflet 5, lucide-react, class-variance-authority, tailwind-merge, clsx
- Node 20-alpine Docker image

**ML package** - pure-Python module (no actual model artifacts, no scikit-learn import in code). Structure: `models/`, `features/`, `pipelines/`, `inference/`, `training/`.

**Infra**
- docker-compose with 5 services: `db` (PostGIS), `redis`, `backend`, `worker` (Celery), `frontend`
- No CI workflow files present (README mentions one but none in repo)

---

## Features Already Built (working end-to-end)

- **JWT auth + cookie** - `POST /api/v1/auth/{register,login}` (`backend/app/routers/auth.py:29`, `:42`); bcrypt hashing; rate-limited 5/min and 10/min via slowapi. Issues token in JSON body **and** sets httponly cookie.
- **`get_current_user` dependency** - accepts `Authorization: Bearer` or cookie (`backend/app/utils/dependencies.py:33`).
- **Admin gate** - `require_admin` (`backend/app/utils/dependencies.py:57`).
- **Farm CRUD (create + list)** - `POST /api/v1/farms`, `GET /api/v1/farms` (`backend/app/routers/farms.py`); stores as Geography POINT with lat/lng; computes centroid via `ST_Y`/`ST_X`.
- **Snapshot endpoints** - `POST/GET /api/v1/analytics/farms/{id}/snapshot[s]` (`backend/app/routers/analytics.py:44`, `:57`).
- **Yield endpoint** - `POST /api/v1/analytics/farms/{id}/yield` (`backend/app/routers/analytics.py:69`); triggers Celery forecast.
- **Risk endpoints** - `POST/GET /api/v1/analytics/farms/{id}/risks` (`backend/app/routers/analytics.py:82`, `:95`).
- **AI Copilot chat** - `POST /api/v1/copilot/chat` (`backend/app/routers/copilot.py:36`); uses OpenAI SDK pointed at Groq (`llama-3.3-70b-versatile`); loads farm + latest snapshot + open risks as context.
- **Admin dashboard endpoint** - `GET /api/v1/admin/dashboard` returns totals + 5 most recent snapshots (`backend/app/routers/admin.py:14`).
- **Celery workers** - `compute_yield_forecast` and `run_risk_assessment` tasks (`backend/app/tasks/analytics_tasks.py`); moisture<15 -> high drought risk, temp>35 -> medium heat stress.
- **ML statistical model v1** - formula in `ml/models/statistical_v1.py:11`; feature builder at `ml/features/feature_builder.py`; inference entry `ml/inference/realtime.py:predict()`.
- **CORS + global error handlers + rate-limit middleware** (`backend/app/main.py`).
- **`/health` endpoint** - returns `{"status": "ok"}` (`backend/app/main.py:66`).
- **Storage service** - S3 client with bucket ensure/upload (not wired to any router).
- **Next.js shell** - landing page, login page, `/farms/new` (with Leaflet boundary drawer), `/dashboard/farmer`, `/dashboard/admin`, React Query provider, axios client with bearer-token interceptor.
- **Dockerfiles + docker-compose** for all services.

## Features Partially Built (started but incomplete)

- **Geospatial provider** - `SentinelNasaMockProvider` returns deterministic mock metrics (`backend/app/infrastructure/external/geospatial_provider.py:16`); **never instantiated or injected** anywhere in the active code path.
- **Copilot provider abstraction** - `RuleBasedCopilotProvider` exists (`backend/app/infrastructure/external/copilot_provider.py:6`) but is dead code; the live `CopilotService` calls OpenAI directly.
- **Repositories** - `UserRepository` / `FarmRepository` in `backend/app/infrastructure/repositories/` are unused by the live `services/*` (which use SQLAlchemy `select()` directly).
- **`workers/refresh_geospatial_snapshots`** - placeholder returning a string (`backend/app/workers/tasks.py:5`).
- **`pipelines/training_pipeline.run_training_pipeline`** - returns placeholder string (`ml/pipelines/training_pipeline.py:1`).
- **S3 storage** - `StorageService` class is complete but no route accepts uploads; no presigned URL flow.
- **Frontend `FarmBoundaryMap`** - captures polygon points; **payload sent is `polygon_geojson`** but the active backend only accepts `{name, location:{lat,lng}, area_ha, crop_type}`.
- **Frontend farmer dashboard** - triggers `/snapshot`, `/yield`, `/risks` mutations **with no body**; copilot sends `{question}` instead of `{message, farm_id}`.
- **Admin dashboard frontend** - renders `total_predictions` and `system_health` that the backend **does not return** (backend returns only `total_farms`, `total_users`, `recent_snapshots`).
- **ML `YieldModel` base class** - interface defined (`ml/models/base.py`); only one implementation, no real training data, no model registry, no persisted model artifact.
- **Tests** - `test_health.py` (passes) and `test_prediction_formula.py` (broken import - see Known Issues).

## Features Not Yet Built

- Real Sentinel-2 / NASA POWER integration (only mock provider exists)
- IoT sensor ingestion endpoints / protocols
- Real ML model training (no dataset, no training loop, no model versioning beyond string label)
- Computer-vision crop-disease diagnosis (no image upload pipeline)
- Voice / WhatsApp / SMS channels
- Multilingual NLP for copilot
- Parametric crop insurance workflows
- Carbon credit issuance
- Loan origination / credit scoring
- Loan disbursement, banking APIs
- Marketplace features (farmer <-> buyer)
- Push notifications / alert channels beyond in-DB rows
- User onboarding / email verification / password reset
- Profile management, password change
- Pagination, filtering, search on farm/snapshot/yield/risk lists
- File/image upload UI & backend route
- Historical yield data ingestion pipeline
- Multi-tenant scoping (Agribusiness / Financial Institution roles from PRD not modelled - only `user`/`admin` in `UserRole` enum)
- CI workflow (README claims one - not in repo)
- Alembic migrations directory (dependency is in `requirements.txt` but no `migrations/` folder and no init in `main.py` lifespan)
- Database bootstrap on startup (no `Base.metadata.create_all`, no Alembic run) - `schema.sql` is shipped but never auto-applied

## Database Schema

Two divergent schemas coexist:

**A. `backend/schema.sql` (matches OLD `app/domain/models.py` - never executed by app):**
- `users` - id (SERIAL), email UNIQUE, full_name, hashed_password, role, created_at
- `farms` - id, owner_id, farm_name, crop_type, planting_date, expected_harvest_date, farm_size_ha, polygon_geojson JSONB, boundary geometry(POLYGON,4326)
- `farm_snapshots` - id, farm_id, source, ndvi, vegetation_health_score, rainfall_mm, temperature_c, drought_risk_score, captured_at
- `yield_predictions` - id, farm_id, predicted_yield_ton_ha, confidence_score, contributing_factors JSONB, model_version
- `risk_alerts` - id, farm_id, alert_type, severity, message, recommendation, created_at

**B. Live SQLAlchemy in `backend/app/models/` (no migration runs these):**
- `users` - id (UUID), email, password_hash, name, role (Enum: `user`/`admin`), created_at
- `farms` - id (UUID), owner_id (UUID FK), name, location (Geography POINT 4326), area_ha, crop_type, created_at
- `snapshots` - id (UUID), farm_id, image_url, notes, soil_moisture, temp_c, created_at
- `yields` - id (UUID), farm_id, season, expected_kg_ha, actual_kg_ha, created_at
- `risks` - id (UUID), farm_id, risk_type, severity (Enum: low/medium/high/critical), description, resolved, created_at

The DB is never initialized; `schema.sql` does not match the live models; no Alembic config exists.

## Known Issues

1. **Two parallel backend architectures left in tree** - both fully populated and importable:
   - Old clean-arch: `app/core/`, `app/domain/`, `app/application/`, `app/api/v1/`, `app/infrastructure/{repositories,external}/` (some files), `app/workers/`
   - New flat: `app/config.py`, `app/database.py`, `app/limits.py`, `app/models/`, `app/schemas/`, `app/services/`, `app/routers/`, `app/tasks/`, `app/utils/`, `app/infrastructure/repositories/` (imports the dead old `app.domain.models`)
   - `app/main.py` only uses the new tree; old tree is dead weight that will confuse future devs and AI tools.

2. **Stale repo imports** - `backend/app/infrastructure/repositories/user_repository.py:4` and `farm_repository.py:4` import from `app.domain.models` and `app.infrastructure.external.geospatial_provider` (old tree). Not reached at runtime, but break `import app.infrastructure.repositories` in any tooling.

3. **Celery worker in compose points to wrong module** - `docker-compose.yml:30` runs `app.workers.celery_app.celery_app` (old tree), but the live `AnalyticsService` triggers `compute_yield_forecast` from `app.tasks.analytics_tasks` (new tree). Forecast and risk-assessment tasks will never execute in `docker compose up`.

4. **Frontend <-> backend contract drift (the farm create flow is broken end-to-end):**
   - Frontend posts `{farm_name, crop_type, planting_date, expected_harvest_date, farm_size_ha, polygon_geojson}` (`frontend/src/app/farms/new/page.tsx:42`).
   - Backend `FarmCreate` expects `{name, location:{lat,lng}, area_ha, crop_type}` (`backend/app/schemas/farm.py:12`).
   - Backend returns `name`, `location`, `area_ha` but the dashboard `Farm` type uses `farm_name`, `crop_type` (`frontend/src/app/dashboard/farmer/page.tsx:10`).

5. **Frontend copilot request shape mismatch** - dashboard sends `{question}` (`dashboard/farmer/page.tsx:41`); backend schema requires `{message, farm_id}` (`backend/app/schemas/copilot.py:6`).

6. **Admin dashboard renders fields backend doesn't return** - frontend reads `total_predictions` and `system_health` (`dashboard/admin/page.tsx:10`); backend returns only `total_farms`, `total_users`, `recent_snapshots` (`backend/app/routers/admin.py:36`).

7. **Env var mismatches** - `backend/.env.example` and root `.env.example` use `SECRET_KEY` / `ACCESS_TOKEN_EXPIRE_MINUTES` / `ALLOWED_ORIGINS` / `DATABASE_URL=postgresql+psycopg2://...` (old tree), but `app/config.py` reads `jwt_secret` / `jwt_expires_minutes` / `cors_origins` / `database_url=postgresql+asyncpg://...` (new tree). The shipped env files will not configure the running app. Likewise `REDIS_URL` and `OPENAI_*`/`AWS_*` are only honored in new `config.py`.

8. **Root `.env.example` has typo** - first line is `66# Backend` (line 1) and `DATABASE_URL=postgresql+psycopg2://db/agripulse` has no credentials and the scheme doesn't match the asyncpg driver the app actually uses.

9. **Missing `frontend/.env.example`** - `docs/DEPLOYMENT.md` instructs users to copy it; the file does not exist.

10. **`test_prediction_formula.py` is broken** - imports `from app.application.services.analytics_service import AnalyticsService` (old tree, different signature) (`backend/tests/test_prediction_formula.py:1`). Will fail collection.

11. **No DB bootstrap** - no `Base.metadata.create_all` call in app startup, no Alembic `env.py` / `migrations/` directory, and `schema.sql` is not loaded anywhere. First run against an empty DB will 500.

12. **Default DATABASE_URL points at non-existent host** - `app/config.py:11` defaults to `postgresql+asyncpg://farmuser:changeme@db:5432/farmdb` (different DB name `farmdb` vs compose's `agripulse`).

13. **Copilot base URL misleadingly named** - `openai_base_url` defaults to Groq's endpoint and the model is `llama-3.3-70b-versatile`. Works only if you actually have a Groq key; OpenAI itself will 404. No fallback when key missing beyond 501.

14. **Analytics Celery tasks return strings as results** - `compute_yield_forecast` / `run_risk_assessment` return `"forecast_complete"` etc., but the calling code in `services/analytics_service.py:29,50` uses `.delay()` fire-and-forget; results never read. Also: if `snapshot.soil_moisture` is `None`, the avg calculation crashes (`TypeError: unsupported operand for +`).

15. **Auth cookie not cleared on logout** - no `/auth/logout` endpoint exists; `jwt_cookie_name` set in `auth.py:16` has no corresponding unsetting.

16. **`limits.py` will fail at import time without `REDIS_URL`** - `Limiter(... storage_uri=settings.redis_url)` runs at module import; if Redis is down, app import itself can fail (depending on slowapi version). No in-memory fallback configured.

17. **`requirements.txt` carries unused heavy deps** - `boto3`, `scikit-learn`, `numpy` are imported nowhere in the active code path (only the unused `StorageService` references boto3). They bloat the image.

18. **JWT secret in defaults is unsafe** - `app/config.py:14` falls back to `"change-this-to-a-long-random-secret"` if env unset; combined with the broken `.env.example` wiring, a misconfigured prod deploy could ship with the default.

19. **PRD claims Agribusiness / Financial Institution roles** - `UserRole` enum only has `user`/`admin` (`backend/app/models/enums.py:4`); the four-role RBAC from the README/PRD is unimplemented.

20. **AGENTS.md is in `frontend/` only** - the same Next.js-version warning (and the actual Next.js 16.2 docs in `node_modules/next/dist/docs/`) applies to any Next.js work; consult those before writing frontend code.

---

## Recommended Next Step (Reconciliation)

Before adding new features, recommend a one-pass cleanup that:

1. Delete the dead old clean-arch tree (`app/core/`, `app/domain/`, `app/application/`, `app/api/`, the old `app/workers/`, stale `app/infrastructure/repositories/*` and `app/infrastructure/external/*`).
2. Fix `docker-compose.yml` worker command to `app.tasks.celery_app.celery_app`.
3. Align `Farm` data model: pick **polygon_geojson + boundary POLYGON** (matches `schema.sql`, `FarmBoundaryMap`, and PRD) and update `app/models/farm.py` + `schemas/farm.py` accordingly.
4. Rewrite `.env.example` files to match `app/config.py` field names and asyncpg DSN.
5. Add `frontend/.env.example`.
6. Initialize Alembic; generate the first migration from current models; call it on container start.
7. Add a `/auth/logout` endpoint and fix the frontend contracts for `farms`, `copilot`, and `admin/dashboard`.
8. Remove unused deps (`boto3`, `scikit-learn`, `numpy`) or actually use them.
9. Fix the analytics task `None` arithmetic bug.
10. Add a `tests/conftest.py` fixture for an async DB session; rewrite `test_prediction_formula.py` against the live `ml.models.statistical_v1`.
