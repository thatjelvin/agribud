# AgriPulse AI (MVP)

AgriPulse AI is an agricultural intelligence platform delivering farm geospatial analytics, yield prediction, risk alerts, and AI copilot assistance.

## MVP Scope

- JWT authentication + cookie + RBAC for `farmer`, `agribusiness`, `financial_institution`, and `admin` roles
- Farm creation with polygon boundary, crop type, planting/harvest dates, and PostGIS persistence
- Geospatial snapshot ingestion (NDVI, vegetation health, rainfall, temperature, drought risk) via a swappable provider abstraction; a deterministic mock is shipped for MVP and is replaced with Sentinel-2/NASA POWER adapters in production
- Yield prediction v1 (statistical baseline behind a `YieldModel` interface) with confidence and contributing factors
- Risk intelligence (drought, heat stress, weather anomaly) emitted as alerts with severity and recommendations
- AI copilot chat endpoint via a vendor-agnostic OpenAI-compatible client (Groq by default, swap to OpenAI or any compatible provider)
- Farmer and Admin dashboards in Next.js 16 (App Router, React Query, Leaflet)
- Docker + Compose, Alembic migrations, environment templates, deployment + API docs

## Repository Structure

- `backend/`  FastAPI + SQLAlchemy 2 (async) + PostGIS + Celery. Alembic in `backend/alembic/`.
- `frontend/` Next.js 16 App Router (TypeScript, Tailwind 4, React Query, Leaflet).
- `ml/`       `YieldModel` interface + `StatisticalYieldModelV1` + feature builder + inference entry. Designed to add CNN/LSTM/Transformer models behind the same interface.
- `docs/`     API and deployment documentation.
- `diagrams/` System architecture diagram source.

## Quick Start

```bash
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local

docker compose up --build
```

- Frontend: http://localhost:3000
- API docs: http://localhost:8000/docs

## Development

### Backend
```bash
cd backend
pip install -r requirements.txt
pytest            # 22 tests, no DB required
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm ci
npm run lint
npm run build
npm run dev
```

## Out of MVP (per `IMPLEMENTATION_PLAN.md`)

- Loan origination, banking integrations
- Parametric insurance, carbon credit workflows
- WhatsApp, voice AI, IoT sensor ingestion
- Marketplace and supply-chain features

These are intentionally left out of MVP per the implementation plan; the
PRD and ARCHITECTURE.md describe the longer-term target.

See `IMPLEMENTATION_PLAN.md` and `docs/API.md` for details.
