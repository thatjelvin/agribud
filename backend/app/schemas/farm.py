from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.utils.validators import MAX_FARM_SIZE_HA, clean_short_text


class PolygonGeoJSON(BaseModel):
    """GeoJSON Polygon geometry.

    `coordinates` is a list of linear rings. Each ring is a list of
    [longitude, latitude] pairs. The first ring is the exterior boundary;
    additional rings (if any) are holes. The first and last coordinate of
    each ring must be identical (GeoJSON spec).
    """

    type: str = Field(default="Polygon")
    coordinates: list[list[list[float]]]

    @field_validator("coordinates")
    @classmethod
    def _validate_rings(cls, rings: list[list[list[float]]]) -> list[list[list[float]]]:
        if not rings:
            raise ValueError("Polygon must have at least one ring")
        for ring in rings:
            if len(ring) < 4:
                raise ValueError(
                    "Each ring must have at least 4 positions (3 unique + closing)"
                )
            if ring[0] != ring[-1]:
                raise ValueError("Each ring must be closed (first == last coordinate)")
            for lon, lat in ring:
                if not (-180.0 <= lon <= 180.0):
                    raise ValueError(f"Longitude {lon} out of range")
                if not (-90.0 <= lat <= 90.0):
                    raise ValueError(f"Latitude {lat} out of range")
        return rings


def _clean_farm_name(value: str) -> str:
    return clean_short_text(value, field_name="farm_name")


def _clean_crop_type(value: str) -> str:
    return clean_short_text(value, field_name="crop_type")


class FarmCreate(BaseModel):
    farm_name: str = Field(min_length=1, max_length=255)
    crop_type: str = Field(min_length=1, max_length=120)
    planting_date: date
    expected_harvest_date: date
    farm_size_ha: float = Field(gt=0, le=MAX_FARM_SIZE_HA)
    polygon_geojson: PolygonGeoJSON

    @field_validator("farm_name", mode="before")
    @classmethod
    def _clean_farm_name_field(cls, value: object) -> object:
        if isinstance(value, str):
            return _clean_farm_name(value)
        return value

    @field_validator("crop_type", mode="before")
    @classmethod
    def _clean_crop_type_field(cls, value: object) -> object:
        if isinstance(value, str):
            return _clean_crop_type(value)
        return value

    @field_validator("planting_date")
    @classmethod
    def _planting_date_not_far_past(cls, value: date) -> date:
        if value.year < 1900:
            raise ValueError("planting_date is unrealistically old (year < 1900)")
        return value

    @field_validator("expected_harvest_date")
    @classmethod
    def _harvest_after_planting(cls, harvest: date, info) -> date:
        planting = info.data.get("planting_date")
        if planting and harvest <= planting:
            raise ValueError("expected_harvest_date must be after planting_date")
        return harvest


class FarmOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    owner_id: UUID
    farm_name: str
    crop_type: str
    planting_date: date
    expected_harvest_date: date
    farm_size_ha: float
    polygon_geojson: dict
    created_at: datetime
