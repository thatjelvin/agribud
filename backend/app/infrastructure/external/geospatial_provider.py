from dataclasses import dataclass


@dataclass
class GeospatialMetrics:
    ndvi: float
    rainfall_mm: float
    temperature_c: float


class GeospatialProvider:
    def fetch_metrics(self, polygon_geojson: dict) -> GeospatialMetrics:  # pragma: no cover - interface
        raise NotImplementedError


class SentinelNasaMockProvider(GeospatialProvider):
    """MVP provider abstraction; replace with production Sentinel/NASA adapters."""

    def fetch_metrics(self, polygon_geojson: dict) -> GeospatialMetrics:
        coordinates = polygon_geojson.get('coordinates', [[]])[0]
        point_count = max(len(coordinates), 4)
        ndvi = min(0.9, 0.35 + point_count * 0.02)
        rainfall = max(5.0, 60.0 - point_count)
        temperature = min(42.0, 24.0 + point_count * 0.3)
        return GeospatialMetrics(ndvi=ndvi, rainfall_mm=rainfall, temperature_c=temperature)
