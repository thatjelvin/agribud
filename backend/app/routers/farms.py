from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models import User
from app.schemas.common import Page
from app.schemas.farm import FarmCreate, FarmOut
from app.services.farm_service import FarmService
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/farms", tags=["farms"])

MAX_LIMIT = 200
DEFAULT_LIMIT = 50


@router.post("", response_model=FarmOut, status_code=status.HTTP_201_CREATED)
async def create_farm(
    payload: FarmCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> FarmOut:
    service = FarmService(session)
    farm = await service.create_farm(current_user.id, payload)
    return FarmOut.model_validate(farm)


@router.get("", response_model=Page[FarmOut])
async def list_farms(
    crop_type: str | None = Query(default=None, max_length=120),
    limit: int = Query(default=DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Page[FarmOut]:
    service = FarmService(session)
    items, total = await service.list_farms(
        current_user.id, limit=limit, offset=offset, crop_type=crop_type
    )
    return Page[FarmOut](
        items=[FarmOut.model_validate(f) for f in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{farm_id}", response_model=FarmOut)
async def get_farm(
    farm_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> FarmOut:
    service = FarmService(session)
    farm = await service.get_farm_for_owner(farm_id, current_user.id)
    return FarmOut.model_validate(farm)
