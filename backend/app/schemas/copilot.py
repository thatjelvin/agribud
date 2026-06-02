from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.utils.validators import clean_copilot_message


class CopilotRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    farm_id: UUID | None = None

    @field_validator("message", mode="before")
    @classmethod
    def _clean_message(cls, value: object) -> object:
        if isinstance(value, str):
            return clean_copilot_message(value)
        return value


class CopilotResponse(BaseModel):
    reply: str
    sources: list[str] | None = None
