from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models import User
from app.schemas.common import Page
from app.schemas.sensor import SensorReadingBatch, SensorReadingOut
from app.services.farm_service import FarmService
from app.services.sensor_service import SensorService
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/sensors", tags=["sensors"])

MAX_LIMIT = 500
DEFAULT_LIMIT = 100


@router.post(
    "/farms/{farm_id}/readings",
    response_model=dict,
    status_code=201,
)
async def ingest_readings(
    farm_id: UUID,
    payload: SensorReadingBatch,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    farm_service = FarmService(session)
    await farm_service.get_farm_for_owner(farm_id, current_user.id)
    sensor_service = SensorService(session)
    rows = await sensor_service.ingest_batch(farm_id, payload.readings)
    return {
        "ingested": len(rows),
        "ids": [str(r.id) for r in rows],
    }


@router.get("/farms/{farm_id}/readings", response_model=Page[SensorReadingOut])
async def list_readings(
    farm_id: UUID,
    sensor_type: str | None = Query(default=None, max_length=64),
    limit: int = Query(default=DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Page[SensorReadingOut]:
    farm_service = FarmService(session)
    await farm_service.get_farm_for_owner(farm_id, current_user.id)
    sensor_service = SensorService(session)
    items, total = await sensor_service.list_recent(
        farm_id, sensor_type, limit=limit, offset=offset
    )
    return Page[SensorReadingOut](
        items=[SensorReadingOut.model_validate(r) for r in items],
        total=total,
        limit=limit,
        offset=offset,
    )
