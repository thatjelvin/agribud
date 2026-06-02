from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models import Farm, User, UserRole
from app.schemas.copilot import CopilotRequest, CopilotResponse
from app.services.copilot_service import CopilotService
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/copilot", tags=["copilot"])


def _error(detail: str, code: str) -> dict:
    return {"detail": detail, "code": code}


async def _ensure_farm_access(
    session: AsyncSession,
    farm_id: UUID,
    current_user: User,
) -> None:
    result = await session.execute(select(Farm).where(Farm.id == farm_id))
    farm = result.scalar_one_or_none()
    if not farm or (current_user.role != UserRole.admin and farm.owner_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_error("Farm not found", "FARM_NOT_FOUND"),
        )


@router.post("/chat", response_model=CopilotResponse)
async def chat(
    payload: CopilotRequest,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> CopilotResponse:
    if payload.farm_id:
        await _ensure_farm_access(session, payload.farm_id, current_user)
    service = CopilotService(session)
    reply, sources = await service.chat(payload.message, payload.farm_id)
    return CopilotResponse(reply=reply, sources=sources)
