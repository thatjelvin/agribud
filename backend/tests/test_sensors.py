"""F11 IoT sensor ingestion contract tests."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.schemas.sensor import SensorReadingBatch, SensorReadingCreate


def test_openapi_exposes_sensors_endpoints():
    from app.main import app

    spec = app.openapi()
    paths = spec["paths"]
    assert "/api/v1/sensors/farms/{farm_id}/readings" in paths
    assert "post" in paths["/api/v1/sensors/farms/{farm_id}/readings"]
    assert "get" in paths["/api/v1/sensors/farms/{farm_id}/readings"]


def test_sensor_reading_create_strips_fields():
    r = SensorReadingCreate(
        sensor_type="  soil_moisture  ",
        value=42.5,
        unit="%",
        recorded_at=datetime.now(timezone.utc),
    )
    assert r.sensor_type == "soil_moisture"
    assert r.unit == "%"


def test_sensor_reading_create_rejects_oversized_fields():
    with pytest.raises(ValidationError):
        SensorReadingCreate(
            sensor_type="x" * 65,
            value=1.0,
            unit="%",
            recorded_at=datetime.now(timezone.utc),
        )
    with pytest.raises(ValidationError):
        SensorReadingCreate(
            sensor_type="soil",
            value=1.0,
            unit="x" * 33,
            recorded_at=datetime.now(timezone.utc),
        )


def test_batch_min_and_max_length():
    with pytest.raises(ValidationError):
        SensorReadingBatch(readings=[])
    with pytest.raises(ValidationError):
        SensorReadingBatch(
            readings=[
                SensorReadingCreate(
                    sensor_type="soil",
                    value=1.0,
                    unit="%",
                    recorded_at=datetime.now(timezone.utc),
                )
            ]
            * 501
        )
