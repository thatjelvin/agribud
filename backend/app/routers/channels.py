from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models import User
from app.schemas.channels import WhatsAppInbound, WhatsAppOutbound
from app.services.copilot_service import CopilotService
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/channels", tags=["channels"])


@router.post(
    "/whatsapp/inbound",
    response_model=WhatsAppOutbound,
    status_code=200,
)
async def whatsapp_inbound(
    payload: WhatsAppInbound,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> WhatsAppOutbound:
    """Receive a WhatsApp message and route it through the copilot.

    Auth is required so only trusted services (Twilio adapter or a dev
    proxy) can post here. The future IVR/voice channel will use the same
    pattern under ``/channels/voice/inbound``.
    """
    service = CopilotService(session)
    try:
        result = await service.chat(message=payload.Body, farm_id=None)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "detail": "Copilot backend unavailable",
                "code": "COPILOT_UNAVAILABLE",
            },
        ) from exc
    return WhatsAppOutbound(to=payload.From, body=result.reply)
