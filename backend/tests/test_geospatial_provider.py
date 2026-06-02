"""F15 geospatial provider factory + OpenMeteo contract tests."""

from __future__ import annotations

import pytest

from app.config import settings
from app.services.geospatial_service import (
    GeospatialMetrics,
    OpenMeteoGeospatialProvider,
    SentinelNasaMockProvider,
    _polygon_centroid,
    get_geospatial_provider,
)


def test_polygon_centroid_returns_lat_lng():
    poly = {
        "type": "Polygon",
        "coordinates": [
            [
                [10.0, 20.0],
                [12.0, 20.0],
                [12.0, 22.0],
                [10.0, 22.0],
                [10.0, 20.0],
            ]
        ],
    }
    lat, lng = _polygon_centroid(poly)
    assert abs(lat - 21.0) < 1e-9
    assert abs(lng - 11.0) < 1e-9


def test_get_geospatial_provider_default_is_mock(monkeypatch):
    monkeypatch.setattr(settings, "geospatial_provider", "mock")
    provider = get_geospatial_provider()
    assert isinstance(provider, SentinelNasaMockProvider)


def test_get_geospatial_provider_open_meteo(monkeypatch):
    monkeypatch.setattr(settings, "geospatial_provider", "open_meteo")
    provider = get_geospatial_provider()
    assert isinstance(provider, OpenMeteoGeospatialProvider)


def test_get_geospatial_provider_unknown_falls_back_to_mock(monkeypatch):
    monkeypatch.setattr(settings, "geospatial_provider", "nonsense")
    provider = get_geospatial_provider()
    assert isinstance(provider, SentinelNasaMockProvider)


@pytest.mark.asyncio
async def test_open_meteo_falls_back_to_mock_on_network_error():
    provider = OpenMeteoGeospatialProvider(base_url="http://127.0.0.1:1", timeout=0.1)
    poly = {
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
    metrics = await provider.fetch_metrics(poly)
    assert isinstance(metrics, GeospatialMetrics)
    assert 0.0 <= metrics.ndvi <= 0.9
    assert 5.0 <= metrics.rainfall_mm <= 60.0
    assert 24.0 <= metrics.temperature_c <= 42.0
    assert 0.0 <= metrics.drought_risk_score <= 1.0


@pytest.mark.asyncio
async def test_open_meteo_parses_response(monkeypatch):
    from app.services import geospatial_service

    class _FakeAsyncClient:
        def __init__(self, *_, **__):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def get(self, url, params):
            class _Resp:
                def raise_for_status(self):
                    return None

                def json(self):
                    return {
                        "current": {"temperature_2m": 26.5, "precipitation": 1.2},
                        "daily": {"precipitation_sum": [12.4]},
                    }

            return _Resp()

    monkeypatch.setattr(geospatial_service.httpx, "AsyncClient", _FakeAsyncClient)
    provider = OpenMeteoGeospatialProvider()
    poly = {
        "type": "Polygon",
        "coordinates": [
            [
                [36.8, -1.3],
                [36.81, -1.3],
                [36.81, -1.29],
                [36.8, -1.29],
                [36.8, -1.3],
            ]
        ],
    }
    metrics = await provider.fetch_metrics(poly)
    assert metrics.temperature_c == 26.5
    assert metrics.rainfall_mm == 12.4
    assert 0.0 < metrics.ndvi <= 0.85
    assert 0.0 <= metrics.drought_risk_score <= 1.0
