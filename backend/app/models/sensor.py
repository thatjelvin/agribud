from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime, Float, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class SensorReading(Base):
    """Generic IoT sensor reading for a farm.

    MVP scope: ingest is a simple HTTP POST (see :mod:`app.routers.sensors`).
    Production (per ARCHITECTURE §3.5) will fan-in via MQTT/LoRaWAN bridges
    and push directly to a time-series store; the SQLAlchemy model is the
    canonical record for backward-compatible query paths.
    """

    __tablename__ = "sensor_readings"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    farm_id: Mapped[UUID] = mapped_column(ForeignKey("farms.id"), index=True)
    sensor_type: Mapped[str] = mapped_column(String(64), index=True)
    value: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(32))
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    extra: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    farm = relationship("Farm", back_populates=None)
