from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models import User
from app.schemas.common import Page
from app.schemas.notification import NotificationOut
from app.services.notification_service import NotificationService
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/notifications", tags=["notifications"])

MAX_LIMIT = 200
DEFAULT_LIMIT = 50


def _error(detail: str, code: str) -> dict:
    return {"detail": detail, "code": code}


@router.get("", response_model=Page[NotificationOut])
async def list_notifications(
    unread_only: bool = Query(default=False),
    limit: int = Query(default=DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Page[NotificationOut]:
    service = NotificationService(session)
    items, total = await service.list_for_user(
        current_user.id, limit=limit, offset=offset, unread_only=unread_only
    )
    return Page[NotificationOut](
        items=[NotificationOut.model_validate(n) for n in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/unread-count")
async def unread_count(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    service = NotificationService(session)
    count = await service.unread_count(current_user.id)
    return {"unread": count}


@router.post("/{notification_id}/read", status_code=status.HTTP_200_OK)
async def mark_read(
    notification_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    service = NotificationService(session)
    ok = await service.mark_read(current_user.id, notification_id)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_error("Notification not found", "NOTIFICATION_NOT_FOUND"),
        )
    return {"id": str(notification_id), "read": True}


@router.post("/mark-all-read", status_code=status.HTTP_200_OK)
async def mark_all_read(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    service = NotificationService(session)
    updated = await service.mark_all_read(current_user.id)
    return {"updated": updated}
