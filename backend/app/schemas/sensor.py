from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.utils.validators import clean_short_text


class SensorReadingCreate(BaseModel):
    sensor_type: str = Field(min_length=1, max_length=64)
    value: float
    unit: str = Field(min_length=1, max_length=32)
    recorded_at: datetime
    extra: dict | None = None

    @field_validator("sensor_type", mode="before")
    @classmethod
    def _clean_sensor_type(cls, value: object) -> object:
        if isinstance(value, str):
            return clean_short_text(value, field_name="sensor_type")
        return value

    @field_validator("unit", mode="before")
    @classmethod
    def _clean_unit(cls, value: object) -> object:
        if isinstance(value, str):
            return clean_short_text(value, field_name="unit")
        return value


class SensorReadingBatch(BaseModel):
    readings: list[SensorReadingCreate] = Field(min_length=1, max_length=500)


class SensorReadingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    farm_id: UUID
    sensor_type: str
    value: float
    unit: str
    recorded_at: datetime
    extra: dict | None = None
    received_at: datetime
