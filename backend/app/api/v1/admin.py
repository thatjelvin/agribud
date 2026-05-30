from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_roles
from app.core.database import get_db
from app.domain.enums import UserRole
from app.domain.models import Farm, User, YieldPrediction

router = APIRouter(prefix='/admin', tags=['admin'])


@router.get('/dashboard')
def admin_dashboard(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.admin)),
):
    total_users = db.scalar(select(func.count(User.id))) or 0
    total_farms = db.scalar(select(func.count(Farm.id))) or 0
    total_predictions = db.scalar(select(func.count(YieldPrediction.id))) or 0
    return {
        'total_users': total_users,
        'total_farms': total_farms,
        'total_predictions': total_predictions,
        'system_health': 'healthy',
    }
