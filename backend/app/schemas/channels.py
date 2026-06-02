from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.utils.validators import clean_copilot_message


class WhatsAppInbound(BaseModel):
    """Twilio WhatsApp webhook payload (relevant subset).

    Twilio POSTs these as application/x-www-form-urlencoded; we accept JSON
    too for easier testing. The field names match Twilio's exactly so the
    production adapter can be a thin passthrough.
    """

    From: str = Field(min_length=1, max_length=64)
    To: str | None = Field(default=None, max_length=64)
    Body: str = Field(min_length=1, max_length=4000)
    ProfileName: str | None = Field(default=None, max_length=120)
    MessageSid: str | None = Field(default=None, max_length=64)

    @field_validator("Body", mode="before")
    @classmethod
    def _clean_body(cls, value: object) -> object:
        if isinstance(value, str):
            return clean_copilot_message(value)
        return value


class WhatsAppOutbound(BaseModel):
    to: str
    body: str
    channel: Literal["whatsapp"] = "whatsapp"
