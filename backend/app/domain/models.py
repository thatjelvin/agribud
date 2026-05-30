from datetime import date, datetime

from geoalchemy2 import Geometry
from sqlalchemy import JSON, Date, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.domain.enums import UserRole


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    farms = relationship('Farm', back_populates='owner')


class Farm(Base):
    __tablename__ = 'farms'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    farm_name: Mapped[str] = mapped_column(String(255), index=True)
    crop_type: Mapped[str] = mapped_column(String(120))
    planting_date: Mapped[date] = mapped_column(Date)
    expected_harvest_date: Mapped[date] = mapped_column(Date)
    farm_size_ha: Mapped[float] = mapped_column(Float)
    polygon_geojson: Mapped[dict] = mapped_column(JSON)
    boundary: Mapped[str | None] = mapped_column(Geometry('POLYGON', srid=4326), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    owner = relationship('User', back_populates='farms')
    snapshots = relationship('FarmSnapshot', back_populates='farm')
    predictions = relationship('YieldPrediction', back_populates='farm')
    alerts = relationship('RiskAlert', back_populates='farm')


class FarmSnapshot(Base):
    __tablename__ = 'farm_snapshots'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    farm_id: Mapped[int] = mapped_column(ForeignKey('farms.id'))
    source: Mapped[str] = mapped_column(String(64), default='sentinel_nasa')
    ndvi: Mapped[float] = mapped_column(Float)
    vegetation_health_score: Mapped[float] = mapped_column(Float)
    rainfall_mm: Mapped[float] = mapped_column(Float)
    temperature_c: Mapped[float] = mapped_column(Float)
    drought_risk_score: Mapped[float] = mapped_column(Float)
    captured_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    farm = relationship('Farm', back_populates='snapshots')


class YieldPrediction(Base):
    __tablename__ = 'yield_predictions'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    farm_id: Mapped[int] = mapped_column(ForeignKey('farms.id'))
    predicted_yield_ton_ha: Mapped[float] = mapped_column(Float)
    confidence_score: Mapped[float] = mapped_column(Float)
    contributing_factors: Mapped[dict] = mapped_column(JSON)
    model_version: Mapped[str] = mapped_column(String(64), default='v1-statistical')
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    farm = relationship('Farm', back_populates='predictions')


class RiskAlert(Base):
    __tablename__ = 'risk_alerts'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    farm_id: Mapped[int] = mapped_column(ForeignKey('farms.id'))
    alert_type: Mapped[str] = mapped_column(String(80), index=True)
    severity: Mapped[str] = mapped_column(String(24), index=True)
    message: Mapped[str] = mapped_column(Text)
    recommendation: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    farm = relationship('Farm', back_populates='alerts')
