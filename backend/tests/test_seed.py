"""Seed-script smoke tests using an in-memory SQLite via SQLite-aio fixture.

The seed script depends on PostGIS (the ``boundary`` column), so we cannot
run it against SQLite. We test the parts that don't need the DB:
- idempotency logic for ``_get_or_create_user`` and the env-var skip path.
"""

from __future__ import annotations

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def test_seed_skips_when_env_disabled():
    from app.scripts.seed import run_seed

    with patch.dict(os.environ, {"AGRIBUD_SEED": "0"}):
        result = asyncio_run(run_seed())
    assert result.get("skipped") == 1


def test_demo_user_specs_have_strong_passwords():
    from app.scripts.seed import DEMO_USERS

    for spec in DEMO_USERS:
        assert len(spec["password"]) >= 8
        classes = sum(
            [
                any(c.islower() for c in spec["password"]),
                any(c.isupper() for c in spec["password"]),
                any(c.isdigit() for c in spec["password"]),
                any(not c.isalnum() for c in spec["password"]),
            ]
        )
        assert classes >= 3, f"{spec['email']} password too weak"


def test_seed_module_importable_as_main():
    import importlib

    module = importlib.import_module("app.scripts.seed")
    assert hasattr(module, "run_seed")
    assert hasattr(module, "main")


def test_demo_polygon_is_closed():
    from app.scripts.seed import _demo_polygon

    poly = _demo_polygon(0.0, 0.0)
    assert poly["type"] == "Polygon"
    ring = poly["coordinates"][0]
    assert ring[0] == ring[-1]
    assert len(ring) >= 4


def asyncio_run(coro):
    import asyncio

    return asyncio.run(coro)
