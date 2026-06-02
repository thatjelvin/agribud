from __future__ import annotations

import json
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Risk, RiskSeverity, Snapshot, Yield
from app.models.enums import RiskSeverity as RiskSeverityEnum
from app.schemas.analytics import RiskCreate, SnapshotCreate
from app.services.geospatial_service import GeospatialService
from app.tasks.analytics_tasks import run_risk_assessment


class AnalyticsService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_snapshot(self, farm, payload: SnapshotCreate) -> Snapshot:
        """Capture a snapshot via the GeospatialService, then enqueue risk assessment."""
        geo = GeospatialService(self.session)
        snapshot = await geo.capture_snapshot(
            farm,
            notes=payload.notes,
            soil_moisture=payload.soil_moisture,
            image_url=payload.image_url,
        )
        run_risk_assessment.delay(str(farm.id))
        return snapshot

    async def list_snapshots(
        self,
        farm_id: UUID,
        *,
        limit: int = 50,
        offset: int = 0,
        since: datetime | None = None,
        source: str | None = None,
    ) -> tuple[list[Snapshot], int]:
        """List snapshots for a farm, paginated, newest first.

        Optional filters: `since` (captured_at >= since), `source`.
        Returns (items, total_count).
        """
        where_clauses = [Snapshot.farm_id == farm_id]
        if since is not None:
            where_clauses.append(Snapshot.captured_at >= since)
        if source is not None:
            where_clauses.append(Snapshot.source == source)

        count_stmt = select(func.count()).select_from(Snapshot).where(*where_clauses)
        total = (await self.session.execute(count_stmt)).scalar_one()

        items_stmt = (
            select(Snapshot)
            .where(*where_clauses)
            .order_by(desc(Snapshot.captured_at))
            .limit(limit)
            .offset(offset)
        )
        items = list((await self.session.execute(items_stmt)).scalars().all())
        return items, int(total)

    async def predict_yield(
        self,
        farm,
        latest_snapshot: Snapshot | None,
        *,
        model_version: str | None = None,
    ) -> Yield:
        """Run the yield model on the latest snapshot and persist the result.

        Imports the ML inference entry lazily to keep the service layer
        free of direct ML package coupling at module-load time.
        """
        from app.config import settings
        from ml.inference.realtime import predict as ml_predict

        snapshot_dict = (
            {
                "ndvi": latest_snapshot.ndvi,
                "vegetation_health_score": latest_snapshot.vegetation_health_score,
                "rainfall_mm": latest_snapshot.rainfall_mm,
                "temperature_c": latest_snapshot.temperature_c,
            }
            if latest_snapshot
            else None
        )
        farm_dict = {
            "farm_size_ha": farm.farm_size_ha,
            "crop_type": farm.crop_type,
        }
        result = ml_predict(
            snapshot_dict,
            farm_dict,
            version=model_version,
            env_model=settings.yield_model,
        )

        season = str(datetime.now(timezone.utc).year)
        entry = Yield(
            farm_id=farm.id,
            season=season,
            predicted_yield_ton_ha=result["predicted_yield_ton_ha"],
            confidence_score=result["confidence_score"],
            contributing_factors=json.loads(json.dumps(result["contributing_factors"])),
            model_version=result["model_version"],
        )
        self.session.add(entry)
        await self.session.commit()
        await self.session.refresh(entry)
        return entry

    async def list_yields(
        self,
        farm_id: UUID,
        *,
        limit: int = 50,
        offset: int = 0,
        season: str | None = None,
        model_version: str | None = None,
    ) -> tuple[list[Yield], int]:
        where_clauses = [Yield.farm_id == farm_id]
        if season is not None:
            where_clauses.append(Yield.season == season)
        if model_version is not None:
            where_clauses.append(Yield.model_version == model_version)

        count_stmt = select(func.count()).select_from(Yield).where(*where_clauses)
        total = (await self.session.execute(count_stmt)).scalar_one()

        items_stmt = (
            select(Yield)
            .where(*where_clauses)
            .order_by(desc(Yield.created_at))
            .limit(limit)
            .offset(offset)
        )
        items = list((await self.session.execute(items_stmt)).scalars().all())
        return items, int(total)

    async def latest_yield(self, farm_id: UUID) -> Yield | None:
        result = await self.session.execute(
            select(Yield)
            .where(Yield.farm_id == farm_id)
            .order_by(desc(Yield.created_at))
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def backfill_yield(
        self, farm_id: UUID, season: str, actual_kg_ha: float, model_version: str
    ) -> Yield:
        """Create a backfill yield row for a past season (no prediction)."""
        entry = Yield(
            farm_id=farm_id,
            season=season,
            predicted_yield_ton_ha=None,
            confidence_score=None,
            contributing_factors=None,
            actual_kg_ha=actual_kg_ha,
            model_version=model_version,
        )
        self.session.add(entry)
        await self.session.commit()
        await self.session.refresh(entry)
        return entry

    async def update_actual_yield(
        self, farm_id: UUID, yield_id: UUID, actual_kg_ha: float
    ) -> Yield | None:
        result = await self.session.execute(
            select(Yield).where(Yield.id == yield_id, Yield.farm_id == farm_id)
        )
        entry = result.scalar_one_or_none()
        if entry is None:
            return None
        entry.actual_kg_ha = actual_kg_ha
        await self.session.commit()
        await self.session.refresh(entry)
        return entry

    async def create_risk(self, farm_id: UUID, payload: RiskCreate) -> Risk:
        entry = Risk(
            farm_id=farm_id,
            alert_type=payload.alert_type,
            severity=RiskSeverity(payload.severity),
            message=payload.message,
            recommendation=payload.recommendation,
        )
        self.session.add(entry)
        await self.session.commit()
        await self.session.refresh(entry)
        from app.services.notification_service import notify_risk_created

        await notify_risk_created(self.session, entry)
        return entry

    async def list_risks(
        self,
        farm_id: UUID,
        *,
        limit: int = 50,
        offset: int = 0,
        resolved: bool | None = None,
        severity: RiskSeverityEnum | None = None,
        alert_type: str | None = None,
    ) -> tuple[list[Risk], int]:
        where_clauses = [Risk.farm_id == farm_id]
        if resolved is not None:
            where_clauses.append(Risk.resolved.is_(resolved))
        if severity is not None:
            where_clauses.append(Risk.severity == RiskSeverity(severity))
        if alert_type is not None:
            where_clauses.append(Risk.alert_type == alert_type)

        count_stmt = select(func.count()).select_from(Risk).where(*where_clauses)
        total = (await self.session.execute(count_stmt)).scalar_one()

        items_stmt = (
            select(Risk)
            .where(*where_clauses)
            .order_by(desc(Risk.created_at))
            .limit(limit)
            .offset(offset)
        )
        items = list((await self.session.execute(items_stmt)).scalars().all())
        return items, int(total)
