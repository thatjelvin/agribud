from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.utils.validators import MAX_URL_LENGTH, clean_short_text_optional


class VisionDiagnoseRequest(BaseModel):
    image_url: str | None = Field(default=None, max_length=MAX_URL_LENGTH)
    image_base64: str | None = Field(default=None, max_length=2_000_000)
    farm_id: UUID | None = None
    notes: str | None = Field(default=None, max_length=2000)

    def _clean_image_url(self) -> str | None:
        return clean_short_text_optional(self.image_url, field_name="image_url")


class VisionDiagnoseResponse(BaseModel):
    diagnosis: str
    confidence: float
    message: str
    recommended_action: str
    model_version: str
    image_hash: str
    created_at: datetime


class VisionDiagnosisOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    farm_id: UUID | None
    image_hash: str
    diagnosis: str
    confidence: float
    recommended_actions: str
    model_version: str
    extra: dict | None = None
    created_at: datetime
