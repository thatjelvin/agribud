from fastapi import HTTPException, status

from app.core.security import create_access_token, get_password_hash, verify_password
from app.domain.models import User
from app.infrastructure.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest


class AuthService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def register(self, payload: RegisterRequest) -> User:
        if self.user_repo.get_by_email(payload.email):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Email already exists')
        user = User(
            email=payload.email,
            full_name=payload.full_name,
            hashed_password=get_password_hash(payload.password),
            role=payload.role,
        )
        return self.user_repo.create(user)

    def login(self, payload: LoginRequest) -> str:
        user = self.user_repo.get_by_email(payload.email)
        if not user or not verify_password(payload.password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid credentials')
        return create_access_token(str(user.id))
