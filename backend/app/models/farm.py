from __future__ import annotations

from datetime import date, datetime
from uuid import UUID, uuid4

from geoalchemy2 import Geometry
from sqlalchemy import JSON, Date, DateTime, Float, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Farm(Base):
    __tablename__ = "farms"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    farm_name: Mapped[str] = mapped_column(String(255), index=True)
    crop_type: Mapped[str] = mapped_column(String(120))
    planting_date: Mapped[date] = mapped_column(Date)
    expected_harvest_date: Mapped[date] = mapped_column(Date)
    farm_size_ha: Mapped[float] = mapped_column(Float)
    polygon_geojson: Mapped[dict] = mapped_column(JSON)
    boundary: Mapped[str | None] = mapped_column(
        Geometry(geometry_type="POLYGON", srid=4326), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    owner = relationship("User", back_populates="farms")
    snapshots = relationship(
        "Snapshot", back_populates="farm", cascade="all, delete-orphan"
    )
    yields = relationship("Yield", back_populates="farm", cascade="all, delete-orphan")
    risks = relationship("Risk", back_populates="farm", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates=None)
