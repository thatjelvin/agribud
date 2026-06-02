from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models import Farm, Risk, RiskSeverity, Snapshot, User, Yield
from app.utils.dependencies import require_role

router = APIRouter(prefix="/lender", tags=["lender"])


@router.get("/overview")
async def overview(
    session: AsyncSession = Depends(get_session),
    _: User = Depends(require_role("financial_institution", "admin")),
) -> dict:
    """Portfolio view: yield forecasts + open risk counts for credit decisions."""
    total_farms = await session.scalar(select(func.count(Farm.id))) or 0
    total_yields = await session.scalar(select(func.count(Yield.id))) or 0
    avg_predicted = await session.scalar(select(func.avg(Yield.predicted_yield_ton_ha)))
    avg_confidence = await session.scalar(select(func.avg(Yield.confidence_score)))

    open_risks = (
        await session.scalar(
            select(func.count(Risk.id)).where(Risk.resolved.is_(False))
        )
        or 0
    )

    severity_rows = await session.execute(
        select(Risk.severity, func.count(Risk.id))
        .where(Risk.resolved.is_(False))
        .group_by(Risk.severity)
    )
    severity_breakdown = {sev.value: int(count) for sev, count in severity_rows.all()}

    high_risk_farms_rows = await session.execute(
        select(
            Farm.farm_name, func.coalesce(func.avg(Snapshot.drought_risk_score), 0.0)
        )
        .join(Snapshot, Snapshot.farm_id == Farm.id)
        .group_by(Farm.id, Farm.farm_name)
        .order_by(func.avg(Snapshot.drought_risk_score).desc())
        .limit(10)
    )
    high_risk_farms = [
        {"farm_name": name, "avg_drought_risk": float(score)}
        for name, score in high_risk_farms_rows.all()
    ]

    return {
        "total_farms": int(total_farms),
        "total_yield_predictions": int(total_yields),
        "avg_predicted_yield_ton_ha": float(avg_predicted) if avg_predicted else None,
        "avg_confidence_score": float(avg_confidence) if avg_confidence else None,
        "open_risks": int(open_risks),
        "severity_breakdown": severity_breakdown,
        "high_risk_farms": high_risk_farms,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
