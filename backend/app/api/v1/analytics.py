from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user
from app.application.services.analytics_service import AnalyticsService
from app.core.database import get_db
from app.domain.enums import UserRole
from app.domain.models import FarmSnapshot, User
from app.infrastructure.external.geospatial_provider import SentinelNasaMockProvider
from app.infrastructure.repositories.farm_repository import FarmRepository
from app.schemas.analytics import RiskAlertOut, SnapshotOut, YieldPredictionOut

router = APIRouter(prefix='/analytics', tags=['analytics'])


@router.post('/farms/{farm_id}/snapshot', response_model=SnapshotOut)
def generate_snapshot(
    farm_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = FarmRepository(db)
    farm = repo.get_farm(farm_id)
    if not farm or (current_user.role != UserRole.admin and farm.owner_id != current_user.id):
        raise HTTPException(status_code=404, detail='Farm not found')
    service = AnalyticsService(repo, SentinelNasaMockProvider())
    return service.generate_snapshot(farm)


@router.get('/farms/{farm_id}/snapshots', response_model=list[SnapshotOut])
def list_snapshots(
    farm_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = FarmRepository(db)
    farm = repo.get_farm(farm_id)
    if not farm or (current_user.role != UserRole.admin and farm.owner_id != current_user.id):
        raise HTTPException(status_code=404, detail='Farm not found')
    return repo.list_snapshots(farm_id)


@router.post('/farms/{farm_id}/yield', response_model=YieldPredictionOut)
def predict_yield(
    farm_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = FarmRepository(db)
    farm = repo.get_farm(farm_id)
    if not farm or (current_user.role != UserRole.admin and farm.owner_id != current_user.id):
        raise HTTPException(status_code=404, detail='Farm not found')
    snapshots = repo.list_snapshots(farm_id)
    latest_snapshot: FarmSnapshot | None = snapshots[0] if snapshots else None
    service = AnalyticsService(repo, SentinelNasaMockProvider())
    return service.predict_yield(farm, latest_snapshot)


@router.post('/farms/{farm_id}/risks', response_model=list[RiskAlertOut])
def generate_risks(
    farm_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = FarmRepository(db)
    farm = repo.get_farm(farm_id)
    if not farm or (current_user.role != UserRole.admin and farm.owner_id != current_user.id):
        raise HTTPException(status_code=404, detail='Farm not found')
    snapshots = repo.list_snapshots(farm_id)
    if not snapshots:
        raise HTTPException(status_code=400, detail='Generate snapshot first')
    service = AnalyticsService(repo, SentinelNasaMockProvider())
    return service.generate_risk_alerts(farm_id, snapshots[0])


@router.get('/farms/{farm_id}/risks', response_model=list[RiskAlertOut])
def list_risks(
    farm_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = FarmRepository(db)
    farm = repo.get_farm(farm_id)
    if not farm or (current_user.role != UserRole.admin and farm.owner_id != current_user.id):
        raise HTTPException(status_code=404, detail='Farm not found')
    return repo.list_alerts(farm_id)
