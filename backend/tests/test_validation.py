"""Input validation hardening (F3) — every request schema rejects malformed
inputs at the API boundary with a 422. These tests pin those contracts.
"""

from __future__ import annotations

from datetime import date

import pytest
from pydantic import ValidationError

from app.schemas.analytics import RiskCreate, SnapshotCreate
from app.schemas.auth import LoginRequest, RegisterRequest
from app.schemas.copilot import CopilotRequest
from app.schemas.farm import FarmCreate, PolygonGeoJSON
from app.schemas.user import UserOut
from app.models.enums import RiskSeverity, UserRole


def _ring(*points: tuple[float, float]) -> list[list[float]]:
    pts = [[lng, lat] for lng, lat in points]
    pts.append(pts[0])
    return pts


# --- Auth -----------------------------------------------------------------


def test_register_accepts_strong_password():
    req = RegisterRequest(
        email="User@Example.COM ",
        password="Str0ng!Pass",
        name="  Jane Farmer  ",
        role=UserRole.agribusiness,
    )
    assert req.email == "user@example.com"
    assert req.name == "Jane Farmer"
    assert req.role == UserRole.agribusiness


def test_register_rejects_short_password():
    with pytest.raises(ValidationError):
        RegisterRequest(email="a@b.com", password="short1!", name="Jane")


def test_register_rejects_password_missing_classes():
    with pytest.raises(ValidationError):
        RegisterRequest(email="a@b.com", password="alllowercase", name="Jane")


def test_register_rejects_blocked_password():
    with pytest.raises(ValidationError):
        RegisterRequest(email="a@b.com", password="password", name="Jane")


def test_register_rejects_whitespace_only_name():
    with pytest.raises(ValidationError):
        RegisterRequest(email="a@b.com", password="Str0ng!Pass", name="   ")


def test_register_rejects_control_char_in_name():
    with pytest.raises(ValidationError):
        RegisterRequest(email="a@b.com", password="Str0ng!Pass", name="Jane\x00Doe")


def test_register_rejects_oversized_name():
    with pytest.raises(ValidationError):
        RegisterRequest(email="a@b.com", password="Str0ng!Pass", name="A" * 256)


def test_register_rejects_invalid_email():
    with pytest.raises(ValidationError):
        RegisterRequest(email="not-an-email", password="Str0ng!Pass", name="Jane")


def test_register_rejects_oversized_email():
    with pytest.raises(ValidationError):
        RegisterRequest(
            email=("a" * 250) + "@b.com",
            password="Str0ng!Pass",
            name="Jane",
        )


def test_login_lowercases_email():
    req = LoginRequest(email="USER@Example.COM  ", password="anything")
    assert req.email == "user@example.com"


# --- Farm -----------------------------------------------------------------


def test_farm_create_rejects_oversized_farm():
    p = PolygonGeoJSON(coordinates=[_ring((0.0, 0.0), (1.0, 0.0), (1.0, 1.0))])
    with pytest.raises(ValidationError):
        FarmCreate(
            farm_name="Big",
            crop_type="Maize",
            planting_date=date(2026, 6, 1),
            expected_harvest_date=date(2026, 10, 1),
            farm_size_ha=200_000.0,
            polygon_geojson=p,
        )


def test_farm_create_rejects_zero_size():
    p = PolygonGeoJSON(coordinates=[_ring((0.0, 0.0), (1.0, 0.0), (1.0, 1.0))])
    with pytest.raises(ValidationError):
        FarmCreate(
            farm_name="Tiny",
            crop_type="Maize",
            planting_date=date(2026, 6, 1),
            expected_harvest_date=date(2026, 10, 1),
            farm_size_ha=0,
            polygon_geojson=p,
        )


def test_farm_create_rejects_negative_size():
    p = PolygonGeoJSON(coordinates=[_ring((0.0, 0.0), (1.0, 0.0), (1.0, 1.0))])
    with pytest.raises(ValidationError):
        FarmCreate(
            farm_name="Neg",
            crop_type="Maize",
            planting_date=date(2026, 6, 1),
            expected_harvest_date=date(2026, 10, 1),
            farm_size_ha=-1.0,
            polygon_geojson=p,
        )


def test_farm_create_rejects_planting_before_1900():
    p = PolygonGeoJSON(coordinates=[_ring((0.0, 0.0), (1.0, 0.0), (1.0, 1.0))])
    with pytest.raises(ValidationError):
        FarmCreate(
            farm_name="Old",
            crop_type="Maize",
            planting_date=date(1899, 1, 1),
            expected_harvest_date=date(2026, 10, 1),
            farm_size_ha=1.0,
            polygon_geojson=p,
        )


def test_farm_create_strips_and_validates_name():
    p = PolygonGeoJSON(coordinates=[_ring((0.0, 0.0), (1.0, 0.0), (1.0, 1.0))])
    f = FarmCreate(
        farm_name="  My Farm  ",
        crop_type="  Maize  ",
        planting_date=date(2026, 6, 1),
        expected_harvest_date=date(2026, 10, 1),
        farm_size_ha=2.0,
        polygon_geojson=p,
    )
    assert f.farm_name == "My Farm"
    assert f.crop_type == "Maize"


def test_farm_create_rejects_whitespace_only_name():
    p = PolygonGeoJSON(coordinates=[_ring((0.0, 0.0), (1.0, 0.0), (1.0, 1.0))])
    with pytest.raises(ValidationError):
        FarmCreate(
            farm_name="   ",
            crop_type="Maize",
            planting_date=date(2026, 6, 1),
            expected_harvest_date=date(2026, 10, 1),
            farm_size_ha=2.0,
            polygon_geojson=p,
        )


def test_farm_create_rejects_oversized_name():
    p = PolygonGeoJSON(coordinates=[_ring((0.0, 0.0), (1.0, 0.0), (1.0, 1.0))])
    with pytest.raises(ValidationError):
        FarmCreate(
            farm_name="N" * 256,
            crop_type="Maize",
            planting_date=date(2026, 6, 1),
            expected_harvest_date=date(2026, 10, 1),
            farm_size_ha=2.0,
            polygon_geojson=p,
        )


# --- Analytics: Snapshot / Risk -----------------------------------------


def test_snapshot_create_cleans_notes():
    s = SnapshotCreate(notes="  Healthy growth observed.  ")
    assert s.notes == "Healthy growth observed."


def test_snapshot_create_rejects_oversized_notes():
    with pytest.raises(ValidationError):
        SnapshotCreate(notes="x" * 2001)


def test_snapshot_create_rejects_oversized_image_url():
    with pytest.raises(ValidationError):
        SnapshotCreate(image_url="https://x.com/" + ("a" * 2100))


def test_snapshot_create_rejects_nul_in_image_url():
    with pytest.raises(ValidationError):
        SnapshotCreate(image_url="https://x.com/img\x00.png")


def test_snapshot_create_soil_moisture_bounds():
    SnapshotCreate(soil_moisture=0.0)
    SnapshotCreate(soil_moisture=100.0)
    with pytest.raises(ValidationError):
        SnapshotCreate(soil_moisture=-0.1)
    with pytest.raises(ValidationError):
        SnapshotCreate(soil_moisture=100.1)


def test_risk_create_rejects_whitespace_only_message():
    with pytest.raises(ValidationError):
        RiskCreate(
            alert_type="drought",
            severity=RiskSeverity.high,
            message="   ",
            recommendation="Irrigate now",
        )


def test_risk_create_rejects_oversized_fields():
    with pytest.raises(ValidationError):
        RiskCreate(
            alert_type="drought",
            severity=RiskSeverity.high,
            message="m" * 2001,
            recommendation="ok",
        )
    with pytest.raises(ValidationError):
        RiskCreate(
            alert_type="drought",
            severity=RiskSeverity.high,
            message="ok",
            recommendation="r" * 2001,
        )
    with pytest.raises(ValidationError):
        RiskCreate(
            alert_type="a" * 81,
            severity=RiskSeverity.high,
            message="ok",
            recommendation="ok",
        )


def test_risk_create_strips_alert_type():
    r = RiskCreate(
        alert_type="  drought_warning  ",
        severity=RiskSeverity.medium,
        message="  Rainfall below 5mm  ",
        recommendation="  Irrigate  ",
    )
    assert r.alert_type == "drought_warning"
    assert r.message == "Rainfall below 5mm"
    assert r.recommendation == "Irrigate"


# --- Copilot -------------------------------------------------------------


def test_copilot_rejects_empty_message():
    with pytest.raises(ValidationError):
        CopilotRequest(message="")


def test_copilot_rejects_oversized_message():
    with pytest.raises(ValidationError):
        CopilotRequest(message="m" * 4001)


def test_copilot_strips_message():
    req = CopilotRequest(message="  What is my NDVI?  ")
    assert req.message == "What is my NDVI?"


# --- Round-trip: 422 envelope is consistent -----------------------------


def test_pydantic_422_envelope_shape():
    from starlette.testclient import TestClient

    from app.main import app

    with TestClient(app) as client:
        # Use a known-valid path that is rate-limited; auth must not be required
        # to trigger validation. The register endpoint accepts anonymous calls
        # and we send an obviously-bad payload to force a 422.
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "password": "short",
                "name": "",
            },
        )
        assert response.status_code == 422
        body = response.json()
        assert body["code"] == "VALIDATION_ERROR"
        assert "errors" in body
        assert isinstance(body["errors"], list)
        assert len(body["errors"]) >= 1
