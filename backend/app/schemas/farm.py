from datetime import date, datetime

from pydantic import BaseModel, Field


class FarmCreate(BaseModel):
    farm_name: str
    crop_type: str
    planting_date: date
    expected_harvest_date: date
    farm_size_ha: float = Field(gt=0)
    polygon_geojson: dict


class FarmOut(FarmCreate):
    id: int
    owner_id: int
    created_at: datetime

    class Config:
        from_attributes = True
