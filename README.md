# AgriPulse AI (MVP)

AgriPulse AI is an agricultural intelligence platform delivering farm geospatial analytics, yield prediction, risk alerts, and AI copilot assistance.

## MVP Scope Implemented

- JWT authentication + RBAC (Farmer, Agribusiness, Financial Institution, Admin)
- Farm creation with polygon boundary and crop metadata
- Geospatial intelligence snapshots (Sentinel-2/NASA provider abstraction)
- Yield prediction (v1 statistical baseline with confidence + factors)
- Risk intelligence (drought, heat stress, anomaly alerts + recommendations)
- AI copilot chat endpoint via replaceable provider interface
- Farmer and Admin dashboards in Next.js
- Docker, Docker Compose, CI workflow, env templates

## Repository Structure

- `backend/` FastAPI service (clean architecture-inspired layers)
- `frontend/` Next.js app (TypeScript, Tailwind, React Query, shadcn-style UI components)
- `ml/` model/features/pipelines/inference/training layout for future deep learning expansion
- `docs/` API and deployment docs
- `diagrams/` architecture diagram source

## Quick Start

```bash
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local

docker compose up --build
```

- Frontend: http://localhost:3000
- API docs: http://localhost:8000/docs

## Development Commands

### Backend
```bash
cd backend
pip install -r requirements.txt
pytest
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

## Future Modules (Interfaces/Placeholders Only)

- Loan origination and banking integrations
- Insurance and carbon-credit workflows
- Voice/WhatsApp channels
- IoT sensor ingestion and marketplace features

See `IMPLEMENTATION_PLAN.md` for roadmap and tradeoffs.
