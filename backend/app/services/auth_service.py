from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, UserRole
from app.schemas.auth import LoginRequest, RegisterRequest
from app.utils.security import create_access_token, hash_password, verify_password


def _error(detail: str, code: str) -> dict:
    return {"detail": detail, "code": code}


class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def register(self, payload: RegisterRequest) -> tuple[User, str]:
        """Create a new user and issue a JWT carrying their role."""
        existing = await self.session.execute(
            select(User).where(User.email == payload.email)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=_error("Email already exists", "EMAIL_EXISTS"),
            )

        user = User(
            email=payload.email,
            name=payload.name,
            password_hash=hash_password(payload.password),
            role=payload.role,
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        token = create_access_token(str(user.id), role=user.role.value)
        return user, token

    async def login(self, payload: LoginRequest) -> tuple[User, str]:
        """Verify credentials and issue a JWT carrying the user's role."""
        result = await self.session.execute(
            select(User).where(User.email == payload.email)
        )
        user = result.scalar_one_or_none()
        if not user or not verify_password(payload.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=_error("Invalid credentials", "AUTH_INVALID"),
            )
        token = create_access_token(str(user.id), role=user.role.value)
        return user, token
