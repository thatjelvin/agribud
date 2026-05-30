from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user
from app.application.services.copilot_service import CopilotService
from app.core.database import get_db
from app.domain.models import User
from app.infrastructure.external.copilot_provider import RuleBasedCopilotProvider
from app.infrastructure.repositories.farm_repository import FarmRepository
from app.schemas.copilot import CopilotAnswer, CopilotQuestion

router = APIRouter(prefix='/copilot', tags=['copilot'])


@router.post('/chat', response_model=CopilotAnswer)
def chat(
    payload: CopilotQuestion,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    answer = CopilotService(RuleBasedCopilotProvider(), FarmRepository(db)).answer(
        payload.question,
        payload.farm_id,
    )
    return CopilotAnswer(answer=answer, source='rule-based-mvp')
