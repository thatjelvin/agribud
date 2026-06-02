"""Polygon geometry validation and WKT conversion."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.farm import FarmCreate, PolygonGeoJSON
from app.services.farm_service import build_boundary_wkt


def _ring(*points: tuple[float, float]) -> list[list[float]]:
    pts = [[lng, lat] for lng, lat in points]
    pts.append(pts[0])
    return pts


def test_polygon_geojson_validates_rings():
    p = PolygonGeoJSON(coordinates=[_ring((0.0, 0.0), (1.0, 0.0), (1.0, 1.0))])
    assert p.type == "Polygon"
    assert len(p.coordinates) == 1


def test_polygon_rejects_unclosed_ring():
    with pytest.raises(ValidationError):
        PolygonGeoJSON(coordinates=[[[0.0, 0.0], [1.0, 0.0], [1.0, 1.0]]])


def test_polygon_rejects_short_ring():
    with pytest.raises(ValidationError):
        PolygonGeoJSON(coordinates=[[[0.0, 0.0], [1.0, 0.0], [1.0, 0.0]]])


def test_polygon_rejects_out_of_range_longitude():
    with pytest.raises(ValidationError):
        PolygonGeoJSON(coordinates=[_ring((181.0, 0.0), (1.0, 0.0), (1.0, 1.0))])


def test_polygon_rejects_out_of_range_latitude():
    with pytest.raises(ValidationError):
        PolygonGeoJSON(coordinates=[_ring((0.0, 91.0), (1.0, 0.0), (1.0, 1.0))])


def test_polygon_rejects_empty_rings():
    with pytest.raises(ValidationError):
        PolygonGeoJSON(coordinates=[])


def test_build_boundary_wkt_produces_postgis_string():
    p = PolygonGeoJSON(coordinates=[_ring((0.0, 0.0), (1.0, 0.0), (1.0, 1.0))])
    wkt = build_boundary_wkt(p.model_dump())
    srid = wkt.srid
    assert srid == 4326
    assert "POLYGON" in wkt.data.upper()


def test_farm_create_rejects_harvest_before_planting():
    from datetime import date

    p = PolygonGeoJSON(coordinates=[_ring((0.0, 0.0), (1.0, 0.0), (1.0, 1.0))])
    with pytest.raises(ValidationError):
        FarmCreate(
            farm_name="Test",
            crop_type="Maize",
            planting_date=date(2026, 6, 1),
            expected_harvest_date=date(2026, 5, 1),
            farm_size_ha=2.0,
            polygon_geojson=p,
        )


def test_farm_create_accepts_valid_payload():
    from datetime import date

    p = PolygonGeoJSON(coordinates=[_ring((0.0, 0.0), (1.0, 0.0), (1.0, 1.0))])
    f = FarmCreate(
        farm_name="Test",
        crop_type="Maize",
        planting_date=date(2026, 6, 1),
        expected_harvest_date=date(2026, 10, 1),
        farm_size_ha=2.0,
        polygon_geojson=p,
    )
    assert f.farm_size_ha == 2.0
