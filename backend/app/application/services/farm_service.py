from fastapi import HTTPException, status

from app.domain.models import Farm
from app.infrastructure.repositories.farm_repository import FarmRepository
from app.schemas.farm import FarmCreate


class FarmService:
    def __init__(self, farm_repo: FarmRepository):
        self.farm_repo = farm_repo

    def create_farm(self, owner_id: int, payload: FarmCreate) -> Farm:
        farm = Farm(owner_id=owner_id, **payload.model_dump())
        return self.farm_repo.create_farm(farm)

    def list_farms(self, owner_id: int) -> list[Farm]:
        return self.farm_repo.list_farms_for_owner(owner_id)

    def get_farm_owned(self, farm_id: int, owner_id: int) -> Farm:
        farm = self.farm_repo.get_farm(farm_id)
        if not farm or farm.owner_id != owner_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Farm not found')
        return farm
