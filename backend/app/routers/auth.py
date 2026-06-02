from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_session
from app.limits import limiter
from app.schemas.auth import AuthResponse, LoginRequest, RegisterRequest
from app.schemas.user import UserOut
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_auth_cookie(response: Response, token: str) -> None:
    max_age = settings.jwt_expires_minutes * 60
    response.set_cookie(
        settings.jwt_cookie_name,
        token,
        httponly=True,
        samesite="lax",
        secure=settings.environment == "production",
        max_age=max_age,
        path="/",
    )


def _clear_auth_cookie(response: Response) -> None:
    response.delete_cookie(settings.jwt_cookie_name, path="/")


@router.post(
    "/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED
)
@limiter.limit("5/minute")
async def register(
    request: Request,
    payload: RegisterRequest,
    response: Response,
    session: AsyncSession = Depends(get_session),
) -> AuthResponse:
    service = AuthService(session)
    user, token = await service.register(payload)
    _set_auth_cookie(response, token)
    return AuthResponse(user=UserOut.model_validate(user), access_token=token)


@router.post("/login", response_model=AuthResponse)
@limiter.limit("10/minute")
async def login(
    request: Request,
    payload: LoginRequest,
    response: Response,
    session: AsyncSession = Depends(get_session),
) -> AuthResponse:
    service = AuthService(session)
    user, token = await service.login(payload)
    _set_auth_cookie(response, token)
    return AuthResponse(user=UserOut.model_validate(user), access_token=token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response) -> Response:
    """Clear the auth cookie. Idempotent: safe to call when not logged in."""
    _clear_auth_cookie(response)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response
