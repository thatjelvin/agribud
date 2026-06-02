"""Pagination contract tests: schema shape + parameter validation on list endpoints.

These tests pin down the public API contract for F2 (Pagination + Filtering)
without requiring a live database. They cover:

1. ``Page[T]`` schema serialisation / deserialisation roundtrip.
2. ``Query`` parameter validation enforced by the routers (limit/offset bounds).
3. Filter parameters are wired into the OpenAPI schema for documentation
   and client generation.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pytest
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.schemas.analytics import RiskOut, SnapshotOut, YieldOut
from app.schemas.common import Page
from app.schemas.farm import FarmOut


class _Demo(BaseModel):
    id: int
    name: str


def test_page_schema_serialises_with_all_fields():
    page = Page[_Demo](
        items=[_Demo(id=1, name="a"), _Demo(id=2, name="b")],
        total=10,
        limit=2,
        offset=4,
    )
    payload = page.model_dump()
    assert payload == {
        "items": [{"id": 1, "name": "a"}, {"id": 2, "name": "b"}],
        "total": 10,
        "limit": 2,
        "offset": 4,
    }


def test_page_schema_roundtrip_via_model_validate():
    raw: dict[str, Any] = {
        "items": [{"id": 1, "name": "x"}],
        "total": 1,
        "limit": 50,
        "offset": 0,
    }
    page = Page[_Demo].model_validate(raw)
    assert page.total == 1
    assert page.limit == 50
    assert page.offset == 0
    assert page.items[0].name == "x"


def test_page_schema_empty_items_is_valid():
    page = Page[_Demo](items=[], total=0, limit=50, offset=0)
    assert page.items == []
    assert page.total == 0


def _openapi_param(name: str, path: str) -> dict[str, Any] | None:
    spec = app.openapi()
    op = spec["paths"][path].get("get") or spec["paths"][path].get("post")
    if op is None:
        return None
    for p in op.get("parameters", []):
        if p.get("name") == name and p.get("in") == "query":
            return p
    return None


def test_openapi_farms_endpoint_exposes_pagination_query_params():
    assert _openapi_param("limit", "/api/v1/farms") is not None
    assert _openapi_param("offset", "/api/v1/farms") is not None
    assert _openapi_param("crop_type", "/api/v1/farms") is not None


def test_openapi_snapshots_endpoint_exposes_pagination_and_filters():
    assert (
        _openapi_param("limit", "/api/v1/analytics/farms/{farm_id}/snapshots")
        is not None
    )
    assert (
        _openapi_param("offset", "/api/v1/analytics/farms/{farm_id}/snapshots")
        is not None
    )
    assert (
        _openapi_param("since", "/api/v1/analytics/farms/{farm_id}/snapshots")
        is not None
    )
    assert (
        _openapi_param("source", "/api/v1/analytics/farms/{farm_id}/snapshots")
        is not None
    )


def test_openapi_yields_endpoint_exposes_pagination_and_filters():
    assert (
        _openapi_param("limit", "/api/v1/analytics/farms/{farm_id}/yields") is not None
    )
    assert (
        _openapi_param("offset", "/api/v1/analytics/farms/{farm_id}/yields") is not None
    )
    assert (
        _openapi_param("season", "/api/v1/analytics/farms/{farm_id}/yields") is not None
    )
    assert (
        _openapi_param("model_version", "/api/v1/analytics/farms/{farm_id}/yields")
        is not None
    )


def test_openapi_risks_endpoint_exposes_pagination_and_filters():
    assert (
        _openapi_param("limit", "/api/v1/analytics/farms/{farm_id}/risks") is not None
    )
    assert (
        _openapi_param("offset", "/api/v1/analytics/farms/{farm_id}/risks") is not None
    )
    assert (
        _openapi_param("resolved", "/api/v1/analytics/farms/{farm_id}/risks")
        is not None
    )
    assert (
        _openapi_param("severity", "/api/v1/analytics/farms/{farm_id}/risks")
        is not None
    )
    assert (
        _openapi_param("alert_type", "/api/v1/analytics/farms/{farm_id}/risks")
        is not None
    )


def test_list_endpoints_declare_paginated_response_models():
    spec = app.openapi()
    farms_resp = spec["paths"]["/api/v1/farms"]["get"]["responses"]["200"]
    assert "$ref" in farms_resp["content"]["application/json"]["schema"]


def test_page_generic_resolves_for_each_out_schema():
    spec = app.openapi()
    schema_names = {name for name in spec["components"]["schemas"].keys()}
    for out in (FarmOut, SnapshotOut, YieldOut, RiskOut):
        assert out.__name__ in schema_names, f"{out.__name__} missing from OpenAPI"


def _install_validation_stubs():
    """Stub the DB session + auth user for tests that should not touch a database."""
    from app.database import get_session
    from app.utils.dependencies import get_current_user

    class _StubUser:
        id = None
        role = "farmer"

    async def _fake_session():
        yield None

    app.dependency_overrides[get_current_user] = lambda: _StubUser()
    app.dependency_overrides[get_session] = _fake_session


def _clear_validation_stubs():
    from app.database import get_session
    from app.utils.dependencies import get_current_user

    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(get_session, None)


def test_farms_query_limit_rejects_zero_without_db():
    from starlette.testclient import TestClient

    _install_validation_stubs()
    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/farms", params={"limit": 0})
            assert response.status_code == 422, response.text
            assert "limit" in response.text
    finally:
        _clear_validation_stubs()


def test_farms_query_limit_rejects_above_max_without_db():
    from starlette.testclient import TestClient

    _install_validation_stubs()
    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/farms", params={"limit": 201})
            assert response.status_code == 422
            assert "limit" in response.text
    finally:
        _clear_validation_stubs()


def test_farms_query_offset_rejects_negative_without_db():
    from starlette.testclient import TestClient

    _install_validation_stubs()
    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/farms", params={"offset": -1})
            assert response.status_code == 422
    finally:
        _clear_validation_stubs()


def test_farms_list_returns_page_envelope_with_stubbed_service(monkeypatch):
    from uuid import uuid4

    from starlette.testclient import TestClient

    from app.utils.dependencies import get_current_user

    class _StubUser:
        id = uuid4()
        role = "farmer"

    captured: dict[str, Any] = {}

    class _StubService:
        def __init__(self, session: AsyncSession):
            pass

        async def list_farms(self, owner_id, *, limit, offset, crop_type):
            captured["owner_id"] = owner_id
            captured["limit"] = limit
            captured["offset"] = offset
            captured["crop_type"] = crop_type
            return [], 0

    monkeypatch.setattr("app.routers.farms.FarmService", _StubService)
    app.dependency_overrides[get_current_user] = lambda: _StubUser()
    try:
        with TestClient(app) as client:
            response = client.get(
                "/api/v1/farms",
                params={"limit": 25, "offset": 50, "crop_type": "Maize"},
            )
            assert response.status_code == 200, response.text
            body = response.json()
            assert body == {"items": [], "total": 0, "limit": 25, "offset": 50}
            assert captured["limit"] == 25
            assert captured["offset"] == 50
            assert captured["crop_type"] == "Maize"
            assert captured["owner_id"] == _StubUser.id
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def test_analytics_risks_passes_severity_enum(monkeypatch):
    from uuid import uuid4

    from starlette.testclient import TestClient

    from app.models.enums import RiskSeverity
    from app.utils.dependencies import get_current_user

    class _StubUser:
        id = uuid4()
        role = "farmer"

    farm_id = uuid4()
    captured: dict[str, Any] = {}

    class _StubFarmService:
        def __init__(self, session: AsyncSession):
            pass

        async def get_farm_for_owner(self, farm_id, owner_id):
            return object()

    class _StubAnalyticsService:
        def __init__(self, session: AsyncSession):
            pass

        async def list_risks(
            self, farm_id, *, limit, offset, resolved, severity, alert_type
        ):
            captured["limit"] = limit
            captured["offset"] = offset
            captured["resolved"] = resolved
            captured["severity"] = severity
            captured["alert_type"] = alert_type
            return [], 0

    monkeypatch.setattr("app.routers.analytics.FarmService", _StubFarmService)
    monkeypatch.setattr("app.routers.analytics.AnalyticsService", _StubAnalyticsService)
    app.dependency_overrides[get_current_user] = lambda: _StubUser()
    try:
        with TestClient(app) as client:
            response = client.get(
                f"/api/v1/analytics/farms/{farm_id}/risks",
                params={
                    "limit": 10,
                    "offset": 0,
                    "resolved": "true",
                    "severity": RiskSeverity.high.value,
                    "alert_type": "drought",
                },
            )
            assert response.status_code == 200, response.text
            assert captured["limit"] == 10
            assert captured["offset"] == 0
            assert captured["resolved"] is True
            assert captured["severity"] == RiskSeverity.high
            assert captured["alert_type"] == "drought"
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def test_page_generic_typed_items_match_component_schema():
    spec = app.openapi()
    page_schema = spec["components"]["schemas"]["Page_FarmOut_"]
    assert page_schema["properties"]["items"]["items"]["$ref"].endswith("/FarmOut")
    assert "total" in page_schema["properties"]
    assert "limit" in page_schema["properties"]
    assert "offset" in page_schema["properties"]


def test_analytics_snapshot_since_accepts_iso8601():
    from uuid import uuid4

    from starlette.testclient import TestClient

    from app.database import get_session
    from app.utils.dependencies import get_current_user

    class _StubUser:
        id = uuid4()
        role = "farmer"

    async def _fake_session():
        yield None

    app.dependency_overrides[get_current_user] = lambda: _StubUser()
    app.dependency_overrides[get_session] = _fake_session
    try:
        with TestClient(app, raise_server_exceptions=False) as client:
            response = client.get(
                f"/api/v1/analytics/farms/{uuid4()}/snapshots",
                params={"since": "2026-01-01T00:00:00Z"},
            )
            assert response.status_code != 422, response.text
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_session, None)
