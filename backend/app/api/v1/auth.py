from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.application.services.auth_service import AuthService
from app.core.database import get_db
from app.infrastructure.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.schemas.user import UserOut

router = APIRouter(prefix='/auth', tags=['auth'])


@router.post('/register', response_model=UserOut)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    service = AuthService(UserRepository(db))
    return service.register(payload)


@router.post('/login', response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    service = AuthService(UserRepository(db))
    token = service.login(payload)
    return TokenResponse(access_token=token)
