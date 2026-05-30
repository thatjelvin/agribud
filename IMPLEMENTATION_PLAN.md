# AgriPulse AI MVP Implementation Plan

## What will be built (Phase 1 MVP)

- **Core identity and access**: registration, login, JWT auth, RBAC for Farmer, Agribusiness, Financial Institution, Admin.
- **Farm management**: farm creation, polygon boundary capture, farm metadata, crop and season details.
- **Geospatial intelligence (MVP adapters)**: Sentinel-2 and NASA POWER integration layer with NDVI, vegetation health, rainfall, temperature, drought risk snapshot generation and historical storage.
- **Yield prediction engine v1**: baseline feature-engineered statistical model service with confidence and contributing factors.
- **Risk intelligence**: drought, heat stress, weather anomaly alerts and recommendation generation.
- **AI Copilot**: conversational endpoint through provider abstraction (vendor-agnostic interface).
- **Dashboards**: Farmer and Admin dashboards for farm/forecast/risk/system summaries.
- **Operational foundations**: Docker, Compose, env templates, CI workflow, API docs, deployment guide.

## What will not be built in MVP

- Loan origination workflows and banking integration logic
- Insurance and claims automation
- Carbon credit issuance/trading workflows
- WhatsApp, voice AI, IoT ingestion, marketplace, supply chain features

These are represented via interface placeholders and extension points only.

## Architectural decisions

- **Clean architecture boundaries**: domain entities, application services, infrastructure adapters, API layer.
- **Repository pattern + DI** for persistence and external service adapters.
- **Vendor abstraction** for LLM, weather, and satellite providers.
- **ML service modularity** in `/ml/{models,features,pipelines,inference,training}` for upgrade path to CNN/LSTM.
- **Replaceable infrastructure**: Postgres/PostGIS, Redis, S3-compatible storage, Celery workers.
- **Monorepo split**: `backend`, `frontend`, `ml`, and deployment docs.

## Technical tradeoffs

- Start with monolithic FastAPI service containing clean internal boundaries to reduce delivery risk.
- Use baseline statistical prediction for fast iteration while preserving model registry/inference contracts.
- Use lightweight geospatial adapters for deterministic MVP output with clear production replacement hooks.
- Keep frontend focused on farmer/admin core workflows before multi-tenant enterprise interfaces.

## Future roadmap (post-MVP)

1. Integrate production Sentinel processing pipeline and weather forecast enrichment.
2. Upgrade yield models to spatiotemporal deep learning (CNN/LSTM/Transformers).
3. Activate fintech modules (loan, insurance, carbon) using existing interfaces.
4. Add multilingual voice and messaging channels.
5. Introduce multi-region scaling, feature store, streaming ingestion, and enterprise analytics.
