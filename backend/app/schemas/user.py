from datetime import datetime

from pydantic import BaseModel, EmailStr

from app.domain.enums import UserRole


class UserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    role: UserRole
    created_at: datetime

    class Config:
        from_attributes = True
