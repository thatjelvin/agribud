from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import RiskSeverity


class Snapshot(Base):
    """Geospatial/weather snapshot for a farm.

    Fields align with PRD §2.3.1 (Predictive Analytics Core) and §4.1
    (Multi-Modal Data Fusion): NDVI, vegetation health, rainfall, temperature,
    drought risk. Source-derived fields from the geospatial provider; manual
    observations (soil moisture, image URL, notes) are optional supplements.
    """

    __tablename__ = "snapshots"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    farm_id: Mapped[UUID] = mapped_column(ForeignKey("farms.id"), index=True)
    source: Mapped[str] = mapped_column(String(64), default="sentinel_nasa")
    ndvi: Mapped[float] = mapped_column(Float)
    vegetation_health_score: Mapped[float] = mapped_column(Float)
    rainfall_mm: Mapped[float] = mapped_column(Float)
    temperature_c: Mapped[float] = mapped_column(Float)
    drought_risk_score: Mapped[float] = mapped_column(Float)
    soil_moisture: Mapped[float | None] = mapped_column(Float, nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    farm = relationship("Farm", back_populates="snapshots")


class Yield(Base):
    """Yield prediction or observed yield entry for a farm-season.

    `model_version` records which yield model produced the prediction
    (per ML Development Rules: support versioning, retraining, replacement).
    """

    __tablename__ = "yields"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    farm_id: Mapped[UUID] = mapped_column(ForeignKey("farms.id"), index=True)
    season: Mapped[str] = mapped_column(String(120))
    predicted_yield_ton_ha: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    contributing_factors: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    actual_kg_ha: Mapped[float | None] = mapped_column(Float, nullable=True)
    model_version: Mapped[str] = mapped_column(String(64), default="v1-statistical")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    farm = relationship("Farm", back_populates="yields")


class Risk(Base):
    """Risk alert for a farm.

    Fields align with PRD §2.3.1 (Risk Intelligence & Early Warning Systems):
    alert_type, severity, message, recommendation.
    """

    __tablename__ = "risks"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    farm_id: Mapped[UUID] = mapped_column(ForeignKey("farms.id"), index=True)
    alert_type: Mapped[str] = mapped_column(String(80), index=True)
    severity: Mapped[RiskSeverity] = mapped_column(
        Enum(RiskSeverity, name="risk_severity"), index=True
    )
    message: Mapped[str] = mapped_column(Text)
    recommendation: Mapped[str] = mapped_column(Text)
    resolved: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    farm = relationship("Farm", back_populates="risks")
    notifications = relationship("Notification", back_populates=None)
