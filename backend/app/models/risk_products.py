from __future__ import annotations

import enum
from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Date,
    DateTime,
    Enum as SAEnum,
    Float,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class CreditDecision(str, enum.Enum):
    approved = "approved"
    declined = "declined"
    review = "review"


class CoverageType(str, enum.Enum):
    drought = "drought"
    flood = "flood"
    multi_peril = "multi_peril"


class CreditAssessment(Base):
    __tablename__ = "credit_assessments"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    farm_id: Mapped[UUID] = mapped_column(ForeignKey("farms.id"), index=True)
    applicant_name: Mapped[str] = mapped_column(String(255))
    requested_amount: Mapped[float] = mapped_column(Float)
    approved_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    risk_score: Mapped[float] = mapped_column(Float)
    decision: Mapped[CreditDecision] = mapped_column(
        SAEnum(CreditDecision, name="credit_decision"), index=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    farm = relationship("Farm", back_populates=None)


class InsuranceQuote(Base):
    __tablename__ = "insurance_quotes"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    farm_id: Mapped[UUID] = mapped_column(ForeignKey("farms.id"), index=True)
    coverage_type: Mapped[CoverageType] = mapped_column(
        SAEnum(CoverageType, name="coverage_type")
    )
    sum_insured: Mapped[float] = mapped_column(Float)
    premium: Mapped[float] = mapped_column(Float)
    valid_until: Mapped[date] = mapped_column(Date)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    farm = relationship("Farm", back_populates=None)


class CarbonCredit(Base):
    __tablename__ = "carbon_credits"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    farm_id: Mapped[UUID] = mapped_column(ForeignKey("farms.id"), index=True)
    season: Mapped[str] = mapped_column(String(120))
    tonnes_co2: Mapped[float] = mapped_column(Float)
    methodology: Mapped[str] = mapped_column(String(120))
    verified: Mapped[bool] = mapped_column(default=False, index=True)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    farm = relationship("Farm", back_populates=None)
