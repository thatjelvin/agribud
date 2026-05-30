from datetime import datetime

from pydantic import BaseModel


class SnapshotOut(BaseModel):
    id: int
    farm_id: int
    ndvi: float
    vegetation_health_score: float
    rainfall_mm: float
    temperature_c: float
    drought_risk_score: float
    captured_at: datetime

    class Config:
        from_attributes = True


class YieldPredictionOut(BaseModel):
    id: int
    farm_id: int
    predicted_yield_ton_ha: float
    confidence_score: float
    contributing_factors: dict
    model_version: str
    created_at: datetime

    class Config:
        from_attributes = True


class RiskAlertOut(BaseModel):
    id: int
    farm_id: int
    alert_type: str
    severity: str
    message: str
    recommendation: str
    created_at: datetime

    class Config:
        from_attributes = True
