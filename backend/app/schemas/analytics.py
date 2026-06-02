from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import RiskSeverity
from app.utils.validators import (
    MAX_URL_LENGTH,
    clean_alert_type,
    clean_short_text,
    clean_short_text_optional,
)


class SnapshotCreate(BaseModel):
    """Manual snapshot creation.

    Most snapshot fields are populated automatically by the GeospatialService
    from the Sentinel/NASA provider. This schema is reserved for manual
    observation entries (e.g., field scouting notes, soil moisture probes).
    """

    notes: str | None = Field(default=None, max_length=2000)
    soil_moisture: float | None = Field(default=None, ge=0, le=100)
    image_url: str | None = Field(default=None, max_length=MAX_URL_LENGTH)

    @field_validator("notes", mode="before")
    @classmethod
    def _clean_notes(cls, value: object) -> object:
        if value is None or value == "":
            return None
        if isinstance(value, str):
            return clean_short_text_optional(value, field_name="notes")
        return value

    @field_validator("image_url", mode="before")
    @classmethod
    def _clean_image_url(cls, value: object) -> object:
        if value is None or value == "":
            return None
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return None
            if len(stripped) > MAX_URL_LENGTH:
                raise ValueError(
                    f"image_url must be at most {MAX_URL_LENGTH} characters"
                )
            for ch in stripped:
                if ch in {chr(0)}:
                    raise ValueError("image_url must not contain NUL bytes")
            return stripped
        return value


class SnapshotOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    farm_id: UUID
    source: str
    ndvi: float
    vegetation_health_score: float
    rainfall_mm: float
    temperature_c: float
    drought_risk_score: float
    soil_moisture: float | None = None
    image_url: str | None = None
    notes: str | None = None
    captured_at: datetime


class YieldCreate(BaseModel):
    season: str = Field(default_factory=lambda: str(datetime.utcnow().year))


class YieldBackfillCreate(BaseModel):
    """Record an observed historical yield for a past season."""

    season: str = Field(min_length=1, max_length=120)
    actual_kg_ha: float = Field(gt=0, le=100_000)
    model_version: str = Field(default="historical", min_length=1, max_length=64)

    @field_validator("season", mode="before")
    @classmethod
    def _clean_season(cls, value: object) -> object:
        if isinstance(value, str):
            return clean_short_text(value, field_name="season")
        return value


class YieldActualUpdate(BaseModel):
    """Patch an existing yield prediction with the observed actual yield."""

    actual_kg_ha: float = Field(gt=0, le=100_000)


class YieldOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    farm_id: UUID
    season: str
    predicted_yield_ton_ha: float | None = None
    confidence_score: float | None = None
    contributing_factors: dict | None = None
    actual_kg_ha: float | None = None
    model_version: str
    created_at: datetime


class RiskCreate(BaseModel):
    alert_type: str = Field(min_length=1, max_length=80)
    severity: RiskSeverity
    message: str = Field(min_length=1, max_length=2000)
    recommendation: str = Field(min_length=1, max_length=2000)

    @field_validator("alert_type", mode="before")
    @classmethod
    def _clean_alert_type(cls, value: object) -> object:
        if isinstance(value, str):
            return clean_alert_type(value)
        return value

    @field_validator("message", mode="before")
    @classmethod
    def _clean_message(cls, value: object) -> object:
        if isinstance(value, str):
            return clean_short_text(value, field_name="message")
        return value

    @field_validator("recommendation", mode="before")
    @classmethod
    def _clean_recommendation(cls, value: object) -> object:
        if isinstance(value, str):
            return clean_short_text(value, field_name="recommendation")
        return value


class RiskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    farm_id: UUID
    alert_type: str
    severity: RiskSeverity
    message: str
    recommendation: str
    resolved: bool
    created_at: datetime
