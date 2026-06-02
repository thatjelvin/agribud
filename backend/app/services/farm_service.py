from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from geoalchemy2.elements import WKTElement
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Farm
from app.schemas.farm import FarmCreate


def _error(detail: str, code: str) -> dict:
    return {"detail": detail, "code": code}


def _polygon_ring_to_wkt(ring: list[list[float]]) -> str:
    """Convert a GeoJSON ring to a WKT coordinate string: 'x1 y1,x2 y2,...'."""
    return ",".join(f"{x} {y}" for x, y in ring)


def build_boundary_wkt(polygon_geojson: dict) -> WKTElement:
    """Build a PostGIS POLYGON WKT element from a GeoJSON polygon dict.

    Raises ValueError if the GeoJSON is malformed.
    """
    rings = polygon_geojson.get("coordinates") or []
    if not rings:
        raise ValueError("Polygon must contain at least one ring")
    wkt_rings = ", ".join(f"({_polygon_ring_to_wkt(r)})" for r in rings)
    return WKTElement(f"POLYGON({wkt_rings})", srid=4326)


class FarmService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_farm(self, owner_id: UUID, payload: FarmCreate) -> Farm:
        """Create a farm and persist its polygon boundary."""
        boundary = build_boundary_wkt(payload.polygon_geojson.model_dump())
        farm = Farm(
            owner_id=owner_id,
            farm_name=payload.farm_name,
            crop_type=payload.crop_type,
            planting_date=payload.planting_date,
            expected_harvest_date=payload.expected_harvest_date,
            farm_size_ha=payload.farm_size_ha,
            polygon_geojson=payload.polygon_geojson.model_dump(),
            boundary=boundary,
        )
        self.session.add(farm)
        await self.session.commit()
        await self.session.refresh(farm)
        return farm

    async def list_farms(
        self,
        owner_id: UUID,
        *,
        limit: int = 50,
        offset: int = 0,
        crop_type: str | None = None,
    ) -> tuple[list[Farm], int]:
        """List farms owned by the user, paginated, optionally filtered by crop_type.

        Returns (items, total_count).
        """
        where_clauses = [Farm.owner_id == owner_id]
        if crop_type is not None:
            where_clauses.append(Farm.crop_type == crop_type)

        count_stmt = select(func.count()).select_from(Farm).where(*where_clauses)
        total = (await self.session.execute(count_stmt)).scalar_one()

        items_stmt = (
            select(Farm)
            .where(*where_clauses)
            .order_by(Farm.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        items = list((await self.session.execute(items_stmt)).scalars().all())
        return items, int(total)

    async def get_farm_for_owner(self, farm_id: UUID, owner_id: UUID) -> Farm:
        """Fetch a farm and enforce ownership."""
        result = await self.session.execute(select(Farm).where(Farm.id == farm_id))
        farm = result.scalar_one_or_none()
        if not farm or farm.owner_id != owner_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=_error("Farm not found", "FARM_NOT_FOUND"),
            )
        return farm

    async def get_farm_centroid(self, farm_id: UUID) -> tuple[float, float] | None:
        """Return (lat, lng) centroid of a farm boundary, or None if no boundary."""
        result = await self.session.execute(
            select(
                func.ST_Y(func.ST_Centroid(Farm.boundary)).label("lat"),
                func.ST_X(func.ST_Centroid(Farm.boundary)).label("lng"),
            ).where(Farm.id == farm_id)
        )
        row = result.first()
        if not row or row.lat is None or row.lng is None:
            return None
        return float(row.lat), float(row.lng)
