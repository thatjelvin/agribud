from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.risk_products import CoverageType, CreditDecision
from app.utils.validators import clean_short_text


class CreditAssessmentCreate(BaseModel):
    farm_id: UUID
    applicant_name: str = Field(min_length=1, max_length=255)
    requested_amount: float = Field(gt=0, le=10_000_000)
    risk_score: float = Field(ge=0, le=1)
    notes: str | None = Field(default=None, max_length=2000)

    @field_validator("applicant_name", mode="before")
    @classmethod
    def _clean_name(cls, value: object) -> object:
        if isinstance(value, str):
            return clean_short_text(value, field_name="applicant_name")
        return value


class CreditAssessmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    farm_id: UUID
    applicant_name: str
    requested_amount: float
    approved_amount: float | None
    risk_score: float
    decision: CreditDecision
    notes: str | None
    created_at: datetime


class InsuranceQuoteCreate(BaseModel):
    farm_id: UUID
    coverage_type: CoverageType
    sum_insured: float = Field(gt=0, le=10_000_000)
    premium: float = Field(gt=0, le=1_000_000)
    valid_until: date


class InsuranceQuoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    farm_id: UUID
    coverage_type: CoverageType
    sum_insured: float
    premium: float
    valid_until: date
    created_at: datetime


class CarbonCreditCreate(BaseModel):
    farm_id: UUID
    season: str = Field(min_length=1, max_length=120)
    tonnes_co2: float = Field(ge=0, le=10_000)
    methodology: str = Field(min_length=1, max_length=120)
    verified: bool = False

    @field_validator("season", mode="before")
    @classmethod
    def _clean_season(cls, value: object) -> object:
        if isinstance(value, str):
            return clean_short_text(value, field_name="season")
        return value

    @field_validator("methodology", mode="before")
    @classmethod
    def _clean_methodology(cls, value: object) -> object:
        if isinstance(value, str):
            return clean_short_text(value, field_name="methodology")
        return value


class CarbonCreditOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    farm_id: UUID
    season: str
    tonnes_co2: float
    methodology: str
    verified: bool
    created_at: datetime
