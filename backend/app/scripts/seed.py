"""Idempotent dev seed: demo users + farms + analytics.

Run with:
    python -m app.scripts.seed

Set the env var ``AGRIBUD_SEED=1`` (default) to seed. ``AGRIBUD_SEED=0`` skips.
The seed is safe to re-run: every entity is created only if absent.
"""

from __future__ import annotations

import asyncio
import os
from datetime import date, datetime, timedelta, timezone

from geoalchemy2.elements import WKTElement
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import SessionLocal
from app.models import Farm, Risk, RiskSeverity, Snapshot, User, UserRole, Yield
from app.services.geospatial_service import (
    GeospatialService,
    SentinelNasaMockProvider,
)
from app.utils.security import hash_password


DEMO_USERS: list[dict] = [
    {
        "email": "farmer@agribud.dev",
        "name": "Demo Farmer",
        "password": "Grow!Well1",
        "role": UserRole.farmer,
    },
    {
        "email": "buyer@agribud.dev",
        "name": "Demo Buyer",
        "password": "Buy!Local1",
        "role": UserRole.agribusiness,
    },
    {
        "email": "lender@agribud.dev",
        "name": "Demo Lender",
        "password": "Lend!Safe1",
        "role": UserRole.financial_institution,
    },
    {
        "email": "admin@agribud.dev",
        "name": "Demo Admin",
        "password": "Admin!Demo1",
        "role": UserRole.admin,
    },
]


def _demo_polygon(lng: float, lat: float, size: float = 0.01) -> dict:
    return {
        "type": "Polygon",
        "coordinates": [
            [
                [lng, lat],
                [lng + size, lat],
                [lng + size, lat + size],
                [lng, lat + size],
                [lng, lat],
            ]
        ],
    }


def _polygon_wkt(geojson: dict) -> WKTElement:
    rings = geojson["coordinates"]
    parts: list[str] = []
    for ring in rings:
        parts.append("(" + ",".join(f"{x} {y}" for x, y in ring) + ")")
    return WKTElement(f"POLYGON({','.join(parts)})", srid=4326)


async def _get_or_create_user(session: AsyncSession, spec: dict) -> User:
    result = await session.execute(select(User).where(User.email == spec["email"]))
    user = result.scalar_one_or_none()
    if user is not None:
        return user
    user = User(
        email=spec["email"],
        name=spec["name"],
        password_hash=hash_password(spec["password"]),
        role=spec["role"],
    )
    session.add(user)
    await session.flush()
    return user


async def _get_or_create_farm(
    session: AsyncSession, owner: User, name: str, crop: str, lng: float, lat: float
) -> Farm:
    result = await session.execute(
        select(Farm).where(Farm.owner_id == owner.id, Farm.farm_name == name)
    )
    farm = result.scalar_one_or_none()
    if farm is not None:
        return farm
    geo = _demo_polygon(lng, lat)
    today = date.today()
    farm = Farm(
        owner_id=owner.id,
        farm_name=name,
        crop_type=crop,
        planting_date=today - timedelta(days=30),
        expected_harvest_date=today + timedelta(days=90),
        farm_size_ha=2.5,
        polygon_geojson=geo,
        boundary=_polygon_wkt(geo),
    )
    session.add(farm)
    await session.flush()
    return farm


async def _ensure_snapshots(
    session: AsyncSession, farm: Farm, count: int = 3
) -> list[Snapshot]:
    result = await session.execute(select(Snapshot).where(Snapshot.farm_id == farm.id))
    existing = list(result.scalars().all())
    if existing:
        return existing
    geo = GeospatialService(session, provider=SentinelNasaMockProvider())
    created: list[Snapshot] = []
    for days_ago in (10, 5, 1):
        snap = await geo.capture_snapshot(farm)
        snap.captured_at = datetime.now(timezone.utc) - timedelta(days=days_ago)
        session.add(snap)
        created.append(snap)
    await session.flush()
    return created


async def _ensure_yield(session: AsyncSession, farm: Farm) -> Yield | None:
    result = await session.execute(select(Yield).where(Yield.farm_id == farm.id))
    existing = result.scalar_one_or_none()
    if existing is not None:
        return existing
    entry = Yield(
        farm_id=farm.id,
        season=str(date.today().year),
        predicted_yield_ton_ha=4.2,
        confidence_score=0.78,
        contributing_factors={"ndvi": 0.62, "rainfall_mm": 24.0, "temperature_c": 28.0},
        model_version="v1-statistical",
    )
    session.add(entry)
    await session.flush()
    return entry


async def _ensure_risk(session: AsyncSession, farm: Farm) -> Risk | None:
    result = await session.execute(
        select(Risk).where(Risk.farm_id == farm.id, Risk.resolved.is_(False))
    )
    existing = result.scalar_one_or_none()
    if existing is not None:
        return existing
    risk = Risk(
        farm_id=farm.id,
        alert_type="drought_warning",
        severity=RiskSeverity.medium,
        message="Rainfall below seasonal average for the last 7 days.",
        recommendation="Consider supplemental irrigation within 48h.",
        resolved=False,
    )
    session.add(risk)
    await session.flush()
    return risk


async def run_seed() -> dict[str, int]:
    if os.getenv("AGRIBUD_SEED", "1") == "0":
        return {"users": 0, "farms": 0, "skipped": 1}

    counts = {"users": 0, "farms": 0, "snapshots": 0, "yields": 0, "risks": 0}
    async with SessionLocal() as session:
        for spec in DEMO_USERS:
            existed_query = await session.execute(
                select(User).where(User.email == spec["email"])
            )
            existed = existed_query.scalar_one_or_none()
            user = await _get_or_create_user(session, spec)
            if existed is None:
                counts["users"] += 1

            if user.role == UserRole.farmer:
                farm = await _get_or_create_farm(
                    session, user, "Demo Maize Field", "Maize", lng=36.8, lat=-1.3
                )
                if farm.id and not await session.execute(
                    select(Farm).where(
                        Farm.owner_id == user.id, Farm.farm_name == farm.farm_name
                    )
                ):
                    counts["farms"] += 1
                snapshots = await _ensure_snapshots(session, farm)
                counts["snapshots"] += len(snapshots)
                yield_row = await _ensure_yield(session, farm)
                if yield_row is not None:
                    counts["yields"] += 1
                risk_row = await _ensure_risk(session, farm)
                if risk_row is not None:
                    counts["risks"] += 1

        await session.commit()
    return counts


def main() -> None:
    counts = asyncio.run(run_seed())
    print(f"Seed complete: {counts}")


if __name__ == "__main__":
    main()
