from __future__ import annotations

import base64
import hashlib

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models import User, VisionDiagnosis, diagnose_from_hash
from app.schemas.vision import VisionDiagnoseRequest, VisionDiagnoseResponse
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/vision", tags=["vision"])


def _hash_image(url: str | None, b64: str | None) -> str:
    if b64:
        try:
            raw = base64.b64decode(b64, validate=True)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"detail": "Invalid base64 image", "code": "INVALID_IMAGE"},
            ) from exc
    elif url:
        raw = url.encode("utf-8")
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "detail": "Provide image_url or image_base64",
                "code": "IMAGE_REQUIRED",
            },
        )
    return hashlib.sha256(raw).hexdigest()


@router.post("/diagnose", response_model=VisionDiagnoseResponse, status_code=200)
async def diagnose(
    payload: VisionDiagnoseRequest,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> VisionDiagnoseResponse:
    image_hash = _hash_image(payload.image_url, payload.image_base64)
    diagnosis, confidence, message, action = diagnose_from_hash(image_hash)
    entry = VisionDiagnosis(
        farm_id=payload.farm_id,
        image_hash=image_hash,
        diagnosis=diagnosis,
        confidence=confidence,
        recommended_actions=action,
        model_version="v0-mock-vision",
        extra={"notes": payload.notes} if payload.notes else None,
    )
    session.add(entry)
    await session.commit()
    await session.refresh(entry)
    return VisionDiagnoseResponse(
        diagnosis=diagnosis,
        confidence=confidence,
        message=message,
        recommended_action=action,
        model_version="v0-mock-vision",
        image_hash=image_hash,
        created_at=entry.created_at,
    )
