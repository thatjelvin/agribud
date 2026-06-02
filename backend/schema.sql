# Database Schema

The authoritative schema is defined by the SQLAlchemy models in `app/models/*`
and applied through Alembic (`alembic upgrade head`). This file is kept as a
human-readable reference matching `0001_initial.py`.

PostgreSQL + PostGIS extension are required.

```sql
CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TYPE user_role AS ENUM (
  'farmer', 'agribusiness', 'financial_institution', 'admin'
);

CREATE TYPE risk_severity AS ENUM (
  'low', 'medium', 'high', 'critical'
);

CREATE TABLE users (
  id            UUID PRIMARY KEY,
  email         VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  name          VARCHAR(255) NOT NULL,
  role          user_role NOT NULL DEFAULT 'farmer',
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE farms (
  id                    UUID PRIMARY KEY,
  owner_id              UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  farm_name             VARCHAR(255) NOT NULL,
  crop_type             VARCHAR(120) NOT NULL,
  planting_date         DATE NOT NULL,
  expected_harvest_date DATE NOT NULL,
  farm_size_ha          DOUBLE PRECISION NOT NULL,
  polygon_geojson       JSONB NOT NULL,
  boundary              geometry(POLYGON, 4326),
  created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX ix_farms_owner_id  ON farms(owner_id);
CREATE INDEX ix_farms_farm_name ON farms(farm_name);

CREATE TABLE snapshots (
  id                     UUID PRIMARY KEY,
  farm_id                UUID NOT NULL REFERENCES farms(id) ON DELETE CASCADE,
  source                 VARCHAR(64) NOT NULL DEFAULT 'sentinel_nasa',
  ndvi                   DOUBLE PRECISION NOT NULL,
  vegetation_health_score DOUBLE PRECISION NOT NULL,
  rainfall_mm            DOUBLE PRECISION NOT NULL,
  temperature_c          DOUBLE PRECISION NOT NULL,
  drought_risk_score     DOUBLE PRECISION NOT NULL,
  soil_moisture          DOUBLE PRECISION,
  image_url              VARCHAR(512),
  notes                  TEXT,
  captured_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX ix_snapshots_farm_id     ON snapshots(farm_id);
CREATE INDEX ix_snapshots_captured_at ON snapshots(captured_at);

CREATE TABLE yields (
  id                       UUID PRIMARY KEY,
  farm_id                  UUID NOT NULL REFERENCES farms(id) ON DELETE CASCADE,
  season                   VARCHAR(120) NOT NULL,
  predicted_yield_ton_ha   DOUBLE PRECISION,
  confidence_score         DOUBLE PRECISION,
  contributing_factors     JSONB,
  actual_kg_ha             DOUBLE PRECISION,
  model_version            VARCHAR(64) NOT NULL DEFAULT 'v1-statistical',
  created_at               TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX ix_yields_farm_id ON yields(farm_id);

CREATE TABLE risks (
  id              UUID PRIMARY KEY,
  farm_id         UUID NOT NULL REFERENCES farms(id) ON DELETE CASCADE,
  alert_type      VARCHAR(80) NOT NULL,
  severity        risk_severity NOT NULL,
  message         TEXT NOT NULL,
  recommendation  TEXT NOT NULL,
  resolved        BOOLEAN NOT NULL DEFAULT FALSE,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX ix_risks_farm_id    ON risks(farm_id);
CREATE INDEX ix_risks_alert_type ON risks(alert_type);
CREATE INDEX ix_risks_severity   ON risks(severity);
```
