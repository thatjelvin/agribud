from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_session
from app.models import Farm, Risk, Snapshot, User, Yield
from app.utils.dependencies import require_admin

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/dashboard")
async def admin_dashboard(
    session: AsyncSession = Depends(get_session),
    _: User = Depends(require_admin),
) -> dict:
    total_users = await session.scalar(select(func.count(User.id))) or 0
    total_farms = await session.scalar(select(func.count(Farm.id))) or 0
    total_predictions = await session.scalar(select(func.count(Yield.id))) or 0
    open_risks = (
        await session.scalar(
            select(func.count(Risk.id)).where(Risk.resolved.is_(False))
        )
        or 0
    )

    snapshot_result = await session.execute(
        select(Snapshot).order_by(Snapshot.captured_at.desc()).limit(5)
    )
    recent_snapshots = [
        {
            "id": str(snapshot.id),
            "farm_id": str(snapshot.farm_id),
            "source": snapshot.source,
            "ndvi": snapshot.ndvi,
            "drought_risk_score": snapshot.drought_risk_score,
            "captured_at": snapshot.captured_at.isoformat(),
        }
        for snapshot in snapshot_result.scalars().all()
    ]

    return {
        "total_users": int(total_users),
        "total_farms": int(total_farms),
        "total_predictions": int(total_predictions),
        "open_risks": int(open_risks),
        "system_health": "ok",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "recent_snapshots": recent_snapshots,
    }


class YieldModelInfo(BaseModel):
    active: str
    available: list[dict]
    env_var: str


@router.get("/yield-model", response_model=YieldModelInfo)
async def yield_model_info(_: User = Depends(require_admin)) -> YieldModelInfo:
    from ml.models.registry import list_versions

    return YieldModelInfo(
        active=settings.yield_model,
        available=list_versions(),
        env_var="YIELD_MODEL",
    )


class YieldModelSelect(BaseModel):
    version: str = Field(min_length=1, max_length=120)


@router.post("/yield-model", response_model=YieldModelInfo)
async def yield_model_select(
    payload: YieldModelSelect, _: User = Depends(require_admin)
) -> YieldModelInfo:
    from ml.models.registry import list_versions, resolve

    resolve(payload.version)
    settings.yield_model = payload.version
    return YieldModelInfo(
        active=settings.yield_model,
        available=list_versions(),
        env_var="YIELD_MODEL",
    )
