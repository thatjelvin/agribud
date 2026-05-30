CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS users (
  id SERIAL PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  full_name VARCHAR(255) NOT NULL,
  hashed_password VARCHAR(255) NOT NULL,
  role VARCHAR(64) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS farms (
  id SERIAL PRIMARY KEY,
  owner_id INT NOT NULL REFERENCES users(id),
  farm_name VARCHAR(255) NOT NULL,
  crop_type VARCHAR(120) NOT NULL,
  planting_date DATE NOT NULL,
  expected_harvest_date DATE NOT NULL,
  farm_size_ha DOUBLE PRECISION NOT NULL,
  polygon_geojson JSONB NOT NULL,
  boundary geometry(POLYGON, 4326),
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS farm_snapshots (
  id SERIAL PRIMARY KEY,
  farm_id INT NOT NULL REFERENCES farms(id),
  source VARCHAR(64) NOT NULL DEFAULT 'sentinel_nasa',
  ndvi DOUBLE PRECISION NOT NULL,
  vegetation_health_score DOUBLE PRECISION NOT NULL,
  rainfall_mm DOUBLE PRECISION NOT NULL,
  temperature_c DOUBLE PRECISION NOT NULL,
  drought_risk_score DOUBLE PRECISION NOT NULL,
  captured_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS yield_predictions (
  id SERIAL PRIMARY KEY,
  farm_id INT NOT NULL REFERENCES farms(id),
  predicted_yield_ton_ha DOUBLE PRECISION NOT NULL,
  confidence_score DOUBLE PRECISION NOT NULL,
  contributing_factors JSONB NOT NULL,
  model_version VARCHAR(64) NOT NULL DEFAULT 'v1-statistical',
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS risk_alerts (
  id SERIAL PRIMARY KEY,
  farm_id INT NOT NULL REFERENCES farms(id),
  alert_type VARCHAR(80) NOT NULL,
  severity VARCHAR(24) NOT NULL,
  message TEXT NOT NULL,
  recommendation TEXT NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
