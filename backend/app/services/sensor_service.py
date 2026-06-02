from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import SensorReading
from app.schemas.sensor import SensorReadingCreate


class SensorService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def ingest_batch(
        self, farm_id: UUID, readings: list[SensorReadingCreate]
    ) -> list[SensorReading]:
        rows = [
            SensorReading(
                farm_id=farm_id,
                sensor_type=r.sensor_type,
                value=r.value,
                unit=r.unit,
                recorded_at=r.recorded_at,
                extra=r.extra,
            )
            for r in readings
        ]
        self.session.add_all(rows)
        await self.session.commit()
        for r in rows:
            await self.session.refresh(r)
        return rows

    async def list_recent(
        self, farm_id: UUID, sensor_type: str | None, *, limit: int, offset: int
    ) -> tuple[list[SensorReading], int]:
        from sqlalchemy import desc, func

        where = [SensorReading.farm_id == farm_id]
        if sensor_type is not None:
            where.append(SensorReading.sensor_type == sensor_type)
        total = (
            await self.session.execute(
                select(func.count()).select_from(SensorReading).where(*where)
            )
        ).scalar_one()
        items = list(
            (
                await self.session.execute(
                    select(SensorReading)
                    .where(*where)
                    .order_by(desc(SensorReading.recorded_at))
                    .limit(limit)
                    .offset(offset)
                )
            )
            .scalars()
            .all()
        )
        return items, int(total)
