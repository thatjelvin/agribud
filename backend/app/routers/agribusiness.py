from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models import Farm, Risk, Snapshot, User, Yield
from app.utils.dependencies import require_role

router = APIRouter(prefix="/agribusiness", tags=["agribusiness"])


@router.get("/overview")
async def overview(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_role("agribusiness", "admin")),
) -> dict:
    """Aggregate farm + analytics view for offtake buyers."""
    total_farms = await session.scalar(select(func.count(Farm.id))) or 0
    total_area = (
        await session.scalar(select(func.coalesce(func.sum(Farm.farm_size_ha), 0.0)))
        or 0.0
    )
    total_yields = await session.scalar(select(func.count(Yield.id))) or 0
    avg_predicted = await session.scalar(select(func.avg(Yield.predicted_yield_ton_ha)))

    crop_rows = await session.execute(
        select(Farm.crop_type, func.count(Farm.id))
        .group_by(Farm.crop_type)
        .order_by(func.count(Farm.id).desc())
        .limit(10)
    )
    crop_breakdown = [
        {"crop_type": crop, "farm_count": int(count)} for crop, count in crop_rows.all()
    ]

    snapshot_rows = await session.execute(
        select(Snapshot).order_by(Snapshot.captured_at.desc()).limit(5)
    )
    recent_snapshots = [
        {
            "id": str(snap.id),
            "farm_id": str(snap.farm_id),
            "ndvi": snap.ndvi,
            "captured_at": snap.captured_at.isoformat(),
        }
        for snap in snapshot_rows.scalars().all()
    ]

    return {
        "total_farms": int(total_farms),
        "total_area_ha": float(total_area),
        "total_yield_predictions": int(total_yields),
        "avg_predicted_yield_ton_ha": float(avg_predicted) if avg_predicted else None,
        "crop_breakdown": crop_breakdown,
        "recent_snapshots": recent_snapshots,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
