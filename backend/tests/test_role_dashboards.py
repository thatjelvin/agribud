"""F7 role-specific dashboards: agribusiness + lender overview contracts."""

from __future__ import annotations

from app.main import app


def test_openapi_exposes_agribusiness_overview():
    spec = app.openapi()
    paths = spec["paths"]
    assert "/api/v1/agribusiness/overview" in paths
    assert "get" in paths["/api/v1/agribusiness/overview"]


def test_openapi_exposes_lender_overview():
    spec = app.openapi()
    paths = spec["paths"]
    assert "/api/v1/lender/overview" in paths
    assert "get" in paths["/api/v1/lender/overview"]


def test_agribusiness_overview_requires_role():
    from starlette.testclient import TestClient

    from app.database import get_session
    from app.utils.dependencies import get_current_user

    class _StubFarmer:
        id = "stub"
        role = "farmer"

    async def _fake_session():
        yield None

    app.dependency_overrides[get_current_user] = lambda: _StubFarmer()
    app.dependency_overrides[get_session] = _fake_session
    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/agribusiness/overview")
            assert response.status_code == 403
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_session, None)


def test_lender_overview_requires_role():
    from starlette.testclient import TestClient

    from app.database import get_session
    from app.utils.dependencies import get_current_user

    class _StubFarmer:
        id = "stub"
        role = "farmer"

    async def _fake_session():
        yield None

    app.dependency_overrides[get_current_user] = lambda: _StubFarmer()
    app.dependency_overrides[get_session] = _fake_session
    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/lender/overview")
            assert response.status_code == 403
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_session, None)
