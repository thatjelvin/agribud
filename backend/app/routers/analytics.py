from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models import Farm, User
from app.models.enums import RiskSeverity
from app.schemas.analytics import (
    RiskCreate,
    RiskOut,
    SnapshotCreate,
    SnapshotOut,
    YieldActualUpdate,
    YieldBackfillCreate,
    YieldOut,
)
from app.schemas.common import Page
from app.services.analytics_service import AnalyticsService
from app.services.farm_service import FarmService
from app.services.geospatial_service import GeospatialService
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/analytics", tags=["analytics"])

MAX_LIMIT = 200
DEFAULT_LIMIT = 50


def _error(detail: str, code: str) -> dict:
    return {"detail": detail, "code": code}


async def _resolve_farm(
    session: AsyncSession, farm_id: UUID, current_user: User
) -> Farm:
    farm_service = FarmService(session)
    farm = await farm_service.get_farm_for_owner(farm_id, current_user.id)
    return farm


@router.post("/farms/{farm_id}/snapshot", response_model=SnapshotOut)
async def create_snapshot(
    farm_id: UUID,
    payload: SnapshotCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> SnapshotOut:
    farm = await _resolve_farm(session, farm_id, current_user)
    service = AnalyticsService(session)
    snapshot = await service.create_snapshot(farm, payload)
    return SnapshotOut.model_validate(snapshot)


@router.get("/farms/{farm_id}/snapshots", response_model=Page[SnapshotOut])
async def list_snapshots(
    farm_id: UUID,
    since: datetime | None = Query(
        default=None,
        description="Only return snapshots captured at/after this ISO-8601 timestamp",
    ),
    source: str | None = Query(default=None, max_length=64),
    limit: int = Query(default=DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Page[SnapshotOut]:
    await _resolve_farm(session, farm_id, current_user)
    service = AnalyticsService(session)
    items, total = await service.list_snapshots(
        farm_id, limit=limit, offset=offset, since=since, source=source
    )
    return Page[SnapshotOut](
        items=[SnapshotOut.model_validate(s) for s in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("/farms/{farm_id}/yield", response_model=YieldOut)
async def predict_yield(
    farm_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> YieldOut:
    """Run the active yield model on the farm's latest snapshot and persist it.

    Returns 400 if no snapshot exists yet (callers must create a snapshot first).
    """
    farm = await _resolve_farm(session, farm_id, current_user)
    geo = GeospatialService(session)
    latest = await geo.latest_snapshot(farm.id)
    if latest is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=_error(
                "No snapshot available; create a snapshot before requesting a yield prediction.",
                "SNAPSHOT_REQUIRED",
            ),
        )
    service = AnalyticsService(session)
    entry = await service.predict_yield(farm, latest)
    return YieldOut.model_validate(entry)


@router.get("/farms/{farm_id}/yields", response_model=Page[YieldOut])
async def list_yields(
    farm_id: UUID,
    season: str | None = Query(default=None, max_length=120),
    model_version: str | None = Query(default=None, max_length=64),
    limit: int = Query(default=DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Page[YieldOut]:
    await _resolve_farm(session, farm_id, current_user)
    service = AnalyticsService(session)
    items, total = await service.list_yields(
        farm_id,
        limit=limit,
        offset=offset,
        season=season,
        model_version=model_version,
    )
    return Page[YieldOut](
        items=[YieldOut.model_validate(y) for y in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/farms/{farm_id}/yields/backfill", response_model=YieldOut, status_code=201
)
async def backfill_yield(
    farm_id: UUID,
    payload: YieldBackfillCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> YieldOut:
    await _resolve_farm(session, farm_id, current_user)
    service = AnalyticsService(session)
    entry = await service.backfill_yield(
        farm_id,
        season=payload.season,
        actual_kg_ha=payload.actual_kg_ha,
        model_version=payload.model_version,
    )
    return YieldOut.model_validate(entry)


@router.patch("/farms/{farm_id}/yields/{yield_id}", response_model=YieldOut)
async def update_actual_yield(
    farm_id: UUID,
    yield_id: UUID,
    payload: YieldActualUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> YieldOut:
    await _resolve_farm(session, farm_id, current_user)
    service = AnalyticsService(session)
    entry = await service.update_actual_yield(
        farm_id, yield_id, actual_kg_ha=payload.actual_kg_ha
    )
    if entry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_error("Yield not found", "YIELD_NOT_FOUND"),
        )
    return YieldOut.model_validate(entry)


@router.post("/farms/{farm_id}/risks", response_model=RiskOut)
async def create_risk(
    farm_id: UUID,
    payload: RiskCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> RiskOut:
    await _resolve_farm(session, farm_id, current_user)
    service = AnalyticsService(session)
    entry = await service.create_risk(farm_id, payload)
    return RiskOut.model_validate(entry)


@router.get("/farms/{farm_id}/risks", response_model=Page[RiskOut])
async def list_risks(
    farm_id: UUID,
    resolved: bool | None = Query(
        default=None, description="true=resolved only, false=open only, null=all"
    ),
    severity: RiskSeverity | None = Query(default=None),
    alert_type: str | None = Query(default=None, max_length=80),
    limit: int = Query(default=DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Page[RiskOut]:
    await _resolve_farm(session, farm_id, current_user)
    service = AnalyticsService(session)
    items, total = await service.list_risks(
        farm_id,
        limit=limit,
        offset=offset,
        resolved=resolved,
        severity=severity,
        alert_type=alert_type,
    )
    return Page[RiskOut](
        items=[RiskOut.model_validate(r) for r in items],
        total=total,
        limit=limit,
        offset=offset,
    )
