# API Overview

Base URL: `http://localhost:8000`

## Authentication
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`

## Farms
- `POST /api/v1/farms`
- `GET /api/v1/farms`

## Analytics
- `POST /api/v1/analytics/farms/{farm_id}/snapshot`
- `GET /api/v1/analytics/farms/{farm_id}/snapshots`
- `POST /api/v1/analytics/farms/{farm_id}/yield`
- `POST /api/v1/analytics/farms/{farm_id}/risks`
- `GET /api/v1/analytics/farms/{farm_id}/risks`

## Copilot
- `POST /api/v1/copilot/chat`

## Admin
- `GET /api/v1/admin/dashboard`

## OpenAPI
Interactive docs are available at `/docs` and `/redoc` when backend is running.
