"""Geospatial mock provider: returns plausible deterministic metrics."""

from __future__ import annotations

import pytest

from app.services.geospatial_service import (
    GeospatialMetrics,
    SentinelNasaMockProvider,
)


@pytest.mark.asyncio
async def test_mock_provider_returns_metrics():
    provider = SentinelNasaMockProvider()
    geojson = {
        "type": "Polygon",
        "coordinates": [
            [
                [0.0, 0.0],
                [0.01, 0.0],
                [0.01, 0.01],
                [0.0, 0.01],
                [0.0, 0.0],
            ]
        ],
    }
    metrics = await provider.fetch_metrics(geojson)
    assert isinstance(metrics, GeospatialMetrics)
    assert 0.0 <= metrics.ndvi <= 0.9
    assert 5.0 <= metrics.rainfall_mm <= 60.0
    assert 24.0 <= metrics.temperature_c <= 42.0
    assert 0.0 <= metrics.drought_risk_score <= 1.0
    assert 0.0 <= metrics.vegetation_health_score <= 100.0


@pytest.mark.asyncio
async def test_mock_provider_is_deterministic():
    provider = SentinelNasaMockProvider()
    geojson = {
        "type": "Polygon",
        "coordinates": [
            [
                [0.0, 0.0],
                [0.01, 0.0],
                [0.01, 0.01],
                [0.0, 0.01],
                [0.0, 0.0],
            ]
        ],
    }
    a = await provider.fetch_metrics(geojson)
    b = await provider.fetch_metrics(geojson)
    assert a == b
