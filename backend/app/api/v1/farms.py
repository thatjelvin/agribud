from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user
from app.application.services.farm_service import FarmService
from app.core.database import get_db
from app.domain.models import User
from app.infrastructure.repositories.farm_repository import FarmRepository
from app.schemas.farm import FarmCreate, FarmOut

router = APIRouter(prefix='/farms', tags=['farms'])


@router.post('', response_model=FarmOut)
def create_farm(
    payload: FarmCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = FarmService(FarmRepository(db))
    return service.create_farm(current_user.id, payload)


@router.get('', response_model=list[FarmOut])
def list_farms(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = FarmService(FarmRepository(db))
    return service.list_farms(current_user.id)
