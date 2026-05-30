from app.infrastructure.external.copilot_provider import CopilotProvider
from app.infrastructure.repositories.farm_repository import FarmRepository


class CopilotService:
    def __init__(self, provider: CopilotProvider, farm_repo: FarmRepository):
        self.provider = provider
        self.farm_repo = farm_repo

    def answer(self, question: str, farm_id: int | None) -> str:
        context = {}
        if farm_id is not None:
            predictions = []
            farm = self.farm_repo.get_farm(farm_id)
            if farm:
                predictions = farm.predictions
            context['latest_prediction'] = predictions[-1] if predictions else None
        return self.provider.answer(question, context)
