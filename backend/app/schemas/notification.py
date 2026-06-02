from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.notification import NotificationKind
from app.utils.validators import clean_short_text


class NotificationCreate(BaseModel):
    user_id: UUID
    kind: NotificationKind = NotificationKind.system
    title: str = Field(min_length=1, max_length=255)
    body: str = Field(min_length=1, max_length=2000)
    related_farm_id: UUID | None = None
    related_risk_id: UUID | None = None

    @field_validator("title", mode="before")
    @classmethod
    def _clean_title(cls, value: object) -> object:
        if isinstance(value, str):
            return clean_short_text(value, field_name="title")
        return value

    @field_validator("body", mode="before")
    @classmethod
    def _clean_body(cls, value: object) -> object:
        if isinstance(value, str):
            return clean_short_text(value, field_name="body")
        return value


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    kind: NotificationKind
    title: str
    body: str
    related_farm_id: UUID | None = None
    related_risk_id: UUID | None = None
    read: bool
    created_at: datetime
