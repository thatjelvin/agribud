from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Protocol

import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.config import settings
from app.models import Farm, Snapshot


logger = logging.getLogger("agribud.geo")


@dataclass(frozen=True)
class GeospatialMetrics:
    """Metrics returned by a geospatial/weather provider for a farm polygon."""

    ndvi: float
    vegetation_health_score: float
    rainfall_mm: float
    temperature_c: float
    drought_risk_score: float


class GeospatialProvider(Protocol):
    """Vendor-agnostic interface for satellite + weather data sources.

    Per ARCHITECTURE.md §3.3 (Geospatial Processing Engine), real
    implementations will wrap GDAL/Rasterio + Google Earth Engine or
    Sentinel Hub. The MVP uses a deterministic mock for fast iteration.
    """

    async def fetch_metrics(self, polygon_geojson: dict) -> GeospatialMetrics: ...


class SentinelNasaMockProvider:
    """Deterministic mock derived from polygon size.

    Stand-in for Sentinel-2 NDVI + NASA POWER rainfall/temperature feeds.
    Produces plausible values so downstream models, risk rules, and tests
    can run end-to-end without external API access.
    """

    async def fetch_metrics(self, polygon_geojson: dict) -> GeospatialMetrics:
        coordinates = (polygon_geojson.get("coordinates") or [[]])[0]
        point_count = max(len(coordinates), 4)
        ndvi = min(0.9, 0.35 + point_count * 0.02)
        rainfall = max(5.0, 60.0 - point_count)
        temperature = min(42.0, 24.0 + point_count * 0.3)
        vegetation_health = min(100.0, ndvi * 100)
        drought_risk = min(
            1.0, max(0.0, (35.0 - rainfall) / 35.0 + (temperature - 28.0) / 20.0)
        )
        return GeospatialMetrics(
            ndvi=round(ndvi, 4),
            vegetation_health_score=round(vegetation_health, 2),
            rainfall_mm=round(rainfall, 2),
            temperature_c=round(temperature, 2),
            drought_risk_score=round(drought_risk, 4),
        )


def _polygon_centroid(polygon_geojson: dict) -> tuple[float, float]:
    """Return (lat, lng) of the first vertex's averaged first ring.

    Good enough for routing weather API calls; centroid computation lives
    in the DB for snapshot geometry but a fast in-process version avoids
    a DB roundtrip here. The closing vertex (equal to the first) is
    skipped to avoid skewing the average.
    """
    coords = (polygon_geojson.get("coordinates") or [[]])[0]
    if not coords:
        return 0.0, 0.0
    if len(coords) > 1 and coords[0] == coords[-1]:
        coords = coords[:-1]
    if not coords:
        return 0.0, 0.0
    lngs = [p[0] for p in coords]
    lats = [p[1] for p in coords]
    return sum(lats) / len(lats), sum(lngs) / len(lngs)


class OpenMeteoGeospatialProvider:
    """Real public-API provider.

    Uses Open-Meteo's free public forecast API for temperature and
    precipitation; NDVI is derived from a heuristic that mixes rainfall
    sufficiency and temperature delta. Falls back to the mock on any
    network/parse error so the platform never 500s on a third-party
    outage.

    The contract is identical to :class:`SentinelNasaMockProvider`, so
    production swap is a one-line change in
    :func:`get_geospatial_provider`.
    """

    def __init__(self, base_url: str | None = None, timeout: float = 5.0):
        self.base_url = base_url or settings.open_meteo_base_url
        self.timeout = timeout

    async def fetch_metrics(self, polygon_geojson: dict) -> GeospatialMetrics:
        lat, lng = _polygon_centroid(polygon_geojson)
        params = {
            "latitude": f"{lat:.4f}",
            "longitude": f"{lng:.4f}",
            "current": "temperature_2m,precipitation",
            "daily": "precipitation_sum",
            "forecast_days": 1,
            "timezone": "auto",
        }
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(self.base_url, params=params)
                response.raise_for_status()
                data = response.json()
        except (httpx.HTTPError, ValueError, KeyError) as exc:
            logger.warning(
                "open_meteo.fetch_failed",
                extra={"error": str(exc), "fallback": "mock"},
            )
            return await SentinelNasaMockProvider().fetch_metrics(polygon_geojson)

        current = data.get("current") or {}
        daily = data.get("daily") or {}
        precip_daily = (daily.get("precipitation_sum") or [0.0])[0] or 0.0
        temperature = float(current.get("temperature_2m", 28.0))
        rainfall = float(precip_daily)
        ndvi = max(0.05, min(0.85, 0.3 + rainfall / 80.0))
        vegetation_health = round(ndvi * 100, 2)
        drought_risk = round(
            max(0.0, min(1.0, (35.0 - rainfall) / 35.0 + (temperature - 28.0) / 20.0)),
            4,
        )
        return GeospatialMetrics(
            ndvi=round(ndvi, 4),
            vegetation_health_score=vegetation_health,
            rainfall_mm=round(rainfall, 2),
            temperature_c=round(temperature, 2),
            drought_risk_score=drought_risk,
        )


def get_geospatial_provider() -> GeospatialProvider:
    """Build the active geospatial provider from settings.

    Setting ``GEOSPATIAL_PROVIDER=open_meteo`` activates the real API.
    Unknown values fall back to the mock with a logged warning.
    """
    name = (settings.geospatial_provider or "mock").lower()
    if name == "open_meteo":
        return OpenMeteoGeospatialProvider()
    if name != "mock":
        logger.warning(
            "geospatial.unknown_provider",
            extra={"provider": name, "fallback": "mock"},
        )
    return SentinelNasaMockProvider()


class GeospatialService:
    """Orchestrates snapshot creation: provider fetch + manual merge + persist."""

    def __init__(
        self, session: AsyncSession, provider: GeospatialProvider | None = None
    ):
        self.session = session
        self.provider = provider or get_geospatial_provider()

    async def capture_snapshot(
        self,
        farm: Farm,
        *,
        notes: str | None = None,
        soil_moisture: float | None = None,
        image_url: str | None = None,
    ) -> Snapshot:
        """Fetch provider metrics for the farm's polygon and persist a Snapshot."""
        metrics = await self.provider.fetch_metrics(farm.polygon_geojson)
        snapshot = Snapshot(
            farm_id=farm.id,
            source="sentinel_nasa_mock",
            ndvi=metrics.ndvi,
            vegetation_health_score=metrics.vegetation_health_score,
            rainfall_mm=metrics.rainfall_mm,
            temperature_c=metrics.temperature_c,
            drought_risk_score=metrics.drought_risk_score,
            soil_moisture=soil_moisture,
            image_url=image_url,
            notes=notes,
        )
        self.session.add(snapshot)
        await self.session.commit()
        await self.session.refresh(snapshot)
        return snapshot

    async def latest_snapshot(self, farm_id) -> Snapshot | None:
        result = await self.session.execute(
            select(Snapshot)
            .where(Snapshot.farm_id == farm_id)
            .order_by(desc(Snapshot.captured_at))
            .limit(1)
        )
        return result.scalar_one_or_none()
