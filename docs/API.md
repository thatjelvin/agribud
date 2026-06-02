# API Overview

Base URL: `http://localhost:8000`
Interactive docs: `/docs` (Swagger UI) and `/redoc` when the backend is running.

All non-public endpoints require a valid JWT in either:
- `Authorization: Bearer <token>` header, or
- the `access_token` httponly cookie set by `/auth/login` or `/auth/register`.

Roles: `farmer` (default), `agribusiness`, `financial_institution`, `admin`.
Admin-only routes return 403 to non-admin callers.

## Authentication
- `POST /api/v1/auth/register` — `{email, password, name, role?}` -> `{user, access_token}`. Sets cookie.
- `POST /api/v1/auth/login` — `{email, password}` -> `{user, access_token}`. Sets cookie.
- `POST /api/v1/auth/logout` — Clears the auth cookie. 204 No Content.

### Auth payload rules
- `email`: valid email format, ≤254 chars, normalised to lowercase.
- `password` (register only): 8..128 chars, must contain at least 3 of {lowercase, uppercase, digit, symbol}, must not be a blocked value (`password`, `changeme`, `admin123`).
- `name`: 1..255 chars after trim, no control characters.
- `role`: one of `farmer`, `agribusiness`, `financial_institution`, `admin` (default `farmer`).
- `password` (login only): 1..128 chars (server does not reveal which field is wrong).

## Farms
- `POST /api/v1/farms` — Create a farm with a GeoJSON polygon boundary.
- `GET  /api/v1/farms` — List the caller's farms. Supports pagination + filtering (see [Pagination](#pagination)).
- `GET  /api/v1/farms/{farm_id}` — Fetch a single farm (caller must own it).

### Farm payload
```json
{
  "farm_name": "Demo Farm",
  "crop_type": "Maize",
  "planting_date": "2026-06-01",
  "expected_harvest_date": "2026-10-01",
  "farm_size_ha": 2.5,
  "polygon_geojson": {
    "type": "Polygon",
    "coordinates": [[[0,0],[1,0],[1,1],[0,0]]]
  }
}
```

Farm rules:
- `farm_name`: 1..255 chars after trim, no control characters.
- `crop_type`: 1..120 chars after trim, no control characters.
- `planting_date`: year ≥ 1900.
- `expected_harvest_date`: must be strictly after `planting_date`.
- `farm_size_ha`: > 0 and ≤ 100,000.
- `polygon_geojson`: closed ring with ≥4 positions, longitude ∈ [-180, 180], latitude ∈ [-90, 90].

## Analytics
- `POST /api/v1/analytics/farms/{farm_id}/snapshot` — Capture a snapshot. Auto-populates NDVI/vegetation/rainfall/temp/drought-risk from the geospatial provider. Body is optional (`{notes, soil_moisture, image_url}`). Triggers async risk assessment.
- `GET  /api/v1/analytics/farms/{farm_id}/snapshots` — List snapshots (newest first). Supports pagination + filtering (see [Pagination](#pagination)).
- `POST /api/v1/analytics/farms/{farm_id}/yield` — Run the active yield model on the latest snapshot. 400 if no snapshot exists.
- `GET  /api/v1/analytics/farms/{farm_id}/yields` — List yield predictions. Supports pagination + filtering.
- `POST /api/v1/analytics/farms/{farm_id}/risks` — Manually create a risk alert. Body: `{alert_type, severity, message, recommendation}`.
- `GET  /api/v1/analytics/farms/{farm_id}/risks` — List risk alerts (newest first). Supports pagination + filtering.

Analytics payload rules:
- `notes` (snapshot): ≤2000 chars after trim, no control characters; `null`/empty allowed.
- `soil_moisture` (snapshot): 0..100 (percent).
- `image_url` (snapshot): ≤2048 chars, no NUL bytes; `null`/empty allowed.
- `alert_type` (risk): 1..80 chars after trim.
- `message` (risk): 1..2000 chars after trim, no control characters.
- `recommendation` (risk): 1..2000 chars after trim, no control characters.

## Validation

All write endpoints validate input server-side. Validation failures return:

```json
{
  "detail": "Validation error",
  "code": "VALIDATION_ERROR",
  "errors": [
    {
      "type": "value_error",
      "loc": ["body", "password"],
      "msg": "Value error, password must contain at least 3 of: ...",
      "input": "..."
    }
  ]
}
```

The 422 envelope is uniform across the API. Per-endpoint rules are documented in each section above.

## Pagination

All list endpoints return a `Page<T>` envelope:

```json
{
  "items": [ ... ],
  "total": 123,
  "limit": 50,
  "offset": 0
}
```

| Field   | Type  | Notes                                              |
|---------|-------|----------------------------------------------------|
| items   | T[]   | The current page of results.                       |
| total   | int   | Unpaginated row count for the current filter set.  |
| limit   | int   | Echo of the request `limit` (for client display).  |
| offset  | int   | Echo of the request `offset`.                      |

### Common query parameters

| Param   | Type | Default | Bounds   | Notes                                                |
|---------|------|---------|----------|------------------------------------------------------|
| limit   | int  | 50      | 1..200   | Page size.                                           |
| offset  | int  | 0       | ≥0       | Number of items to skip.                             |

### Per-endpoint filters

| Endpoint                                                       | Filters                                                   |
|----------------------------------------------------------------|-----------------------------------------------------------|
| `GET /api/v1/farms`                                            | `crop_type` (string, exact match)                         |
| `GET /api/v1/analytics/farms/{id}/snapshots`                   | `since` (ISO-8601 timestamp), `source`                    |
| `GET /api/v1/analytics/farms/{id}/yields`                      | `season`, `model_version`                                 |
| `GET /api/v1/analytics/farms/{id}/risks`                       | `resolved` (bool), `severity` (`low`/`medium`/`high`/`critical`), `alert_type` |

Example:
```
GET /api/v1/farms?limit=25&offset=0&crop_type=Maize
GET /api/v1/analytics/farms/<id>/risks?resolved=false&severity=high
```

## Copilot
- `POST /api/v1/copilot/chat` — `{message, farm_id?}` -> `{reply, sources?}`. If `OPENAI_API_KEY` is unset, returns 501. The reply is grounded in the farm's latest snapshot, latest yield, and open risks when a `farm_id` is provided.
  - `message`: 1..4000 chars after trim.
  - `farm_id`: optional UUID.

## Admin
- `GET /api/v1/admin/dashboard` — Admin-only. Returns `{total_users, total_farms, total_predictions, open_risks, system_health, generated_at, recent_snapshots[]}`.
- `GET /api/v1/admin/yield-model` — Admin-only. Lists registered yield models + active selection.
- `POST /api/v1/admin/yield-model` — Admin-only. Body: `{version}`. Swaps the active yield model in-process (in-memory only; not persisted across restarts).

## Notifications
- `GET /api/v1/notifications?unread_only=&limit=&offset=` — List the caller's notifications (paginated).
- `GET /api/v1/notifications/unread-count` — `{unread: int}`.
- `POST /api/v1/notifications/{id}/read` — Mark one notification as read.
- `POST /api/v1/notifications/mark-all-read` — Mark all of the caller's notifications as read.

Risks created via the analytics service or the `run_risk_assessment` Celery task fan out a notification to the farm owner automatically.

## Agribusiness (role: `agribusiness` or `admin`)
- `GET /api/v1/agribusiness/overview` — Aggregated farm + yield stats + recent snapshots.

## Lender (role: `financial_institution` or `admin`)
- `GET /api/v1/lender/overview` — Yield forecasts + open risk portfolio + high drought-risk farms.

## Sensors (IoT)
- `POST /api/v1/sensors/farms/{farm_id}/readings` — Ingest a batch (1..500) of sensor readings.
- `GET /api/v1/sensors/farms/{farm_id}/readings?sensor_type=&limit=&offset=` — List recent readings.

Reading shape: `{sensor_type, value, unit, recorded_at, extra?}`.

## Vision
- `POST /api/v1/vision/diagnose` — Body: `{image_url?, image_base64?, farm_id?, notes?}`. Returns a deterministic MVP diagnosis. Hash of either input is stored for audit.

## Channels
- `POST /api/v1/channels/whatsapp/inbound` — Twilio-shaped body (`From`, `Body`, `ProfileName`, `MessageSid`). Proxies the message to the copilot and returns a WhatsApp-shaped reply.

## Risk Products (MVP scaffolds)
- `POST /api/v1/risk-products/credit-assessments` — `{farm_id, applicant_name, requested_amount, risk_score, notes?}`. Decision is auto-derived (`approved` if risk < 0.3, partial if < 0.6, review if < 0.8, declined otherwise).
- `GET /api/v1/risk-products/credit-assessments?decision=&limit=&offset=` — role: `financial_institution` or `admin`.
- `POST /api/v1/risk-products/insurance-quotes` — `{farm_id, coverage_type, sum_insured, premium, valid_until}`.
- `GET /api/v1/risk-products/insurance-quotes` — role: `financial_institution` or `admin`.
- `POST /api/v1/risk-products/carbon-credits` — `{farm_id, season, tonnes_co2, methodology, verified?}`.
- `GET /api/v1/risk-products/carbon-credits?verified=&limit=&offset=` — role: `agribusiness`, `financial_institution`, or `admin`.

## Health & metrics
- `GET /health` and `/healthz` — Liveness, always 200.
- `GET /readyz` — Readiness; checks DB and returns `{status, checks: {database}}`.
- `GET /metrics` — Lightweight JSON process metrics (PID, RSS, thread count). Replace with Prometheus client in production.

## Geospatial provider

The active provider is selected by `GEOSPATIAL_PROVIDER` in the backend env:
- `mock` (default) — deterministic values derived from polygon size. Use for tests and offline dev.
- `open_meteo` — real public API; falls back to the mock on any network/parse error so the platform never 500s on third-party outage.
