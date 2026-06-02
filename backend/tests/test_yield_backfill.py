"""F8 historical yield backfill contract tests."""

from __future__ import annotations

from app.main import app


def test_openapi_exposes_backfill_yield():
    spec = app.openapi()
    path = "/api/v1/analytics/farms/{farm_id}/yields/backfill"
    assert path in spec["paths"]
    assert "post" in spec["paths"][path]


def test_openapi_exposes_patch_yield():
    spec = app.openapi()
    path = "/api/v1/analytics/farms/{farm_id}/yields/{yield_id}"
    assert path in spec["paths"]
    assert "patch" in spec["paths"][path]


def test_backfill_payload_validates_season():
    from pydantic import ValidationError

    from app.schemas.analytics import YieldBackfillCreate

    good = YieldBackfillCreate(season="2024", actual_kg_ha=2500.0)
    assert good.season == "2024"

    with pytest.raises(ValidationError):
        YieldBackfillCreate(season="x" * 121, actual_kg_ha=1.0)


def test_backfill_payload_validates_actual_kg_ha():
    from pydantic import ValidationError

    from app.schemas.analytics import YieldBackfillCreate

    with pytest.raises(ValidationError):
        YieldBackfillCreate(season="2024", actual_kg_ha=0)
    with pytest.raises(ValidationError):
        YieldBackfillCreate(season="2024", actual_kg_ha=-1.0)
    with pytest.raises(ValidationError):
        YieldBackfillCreate(season="2024", actual_kg_ha=200_000.0)


def test_actual_update_validates_kg_ha():
    from pydantic import ValidationError

    from app.schemas.analytics import YieldActualUpdate

    good = YieldActualUpdate(actual_kg_ha=3000.0)
    assert good.actual_kg_ha == 3000.0

    with pytest.raises(ValidationError):
        YieldActualUpdate(actual_kg_ha=0)


import pytest
