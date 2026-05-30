from app.domain.models import Farm, FarmSnapshot, RiskAlert, YieldPrediction
from app.infrastructure.external.geospatial_provider import GeospatialProvider
from app.infrastructure.repositories.farm_repository import FarmRepository


class AnalyticsService:
    def __init__(self, farm_repo: FarmRepository, geospatial_provider: GeospatialProvider):
        self.farm_repo = farm_repo
        self.geospatial_provider = geospatial_provider

    def generate_snapshot(self, farm: Farm) -> FarmSnapshot:
        metrics = self.geospatial_provider.fetch_metrics(farm.polygon_geojson)
        vegetation_health = min(100.0, metrics.ndvi * 100)
        drought_score = min(1.0, max(0.0, (35 - metrics.rainfall_mm) / 35 + (metrics.temperature_c - 28) / 20))
        snapshot = FarmSnapshot(
            farm_id=farm.id,
            ndvi=metrics.ndvi,
            vegetation_health_score=vegetation_health,
            rainfall_mm=metrics.rainfall_mm,
            temperature_c=metrics.temperature_c,
            drought_risk_score=drought_score,
        )
        return self.farm_repo.add_snapshot(snapshot)

    def predict_yield(self, farm: Farm, snapshot: FarmSnapshot | None) -> YieldPrediction:
        health = snapshot.vegetation_health_score if snapshot else 55.0
        rainfall = snapshot.rainfall_mm if snapshot else 30.0
        temp = snapshot.temperature_c if snapshot else 30.0
        predicted = max(0.5, 1.2 + (health / 100) * 3.5 + (rainfall / 100) - ((temp - 30) * 0.08))
        confidence = min(0.95, 0.55 + health / 250)
        factors = {
            'vegetation_health_score': health,
            'rainfall_mm': rainfall,
            'temperature_c': temp,
            'crop_type': farm.crop_type,
        }
        prediction = YieldPrediction(
            farm_id=farm.id,
            predicted_yield_ton_ha=predicted,
            confidence_score=confidence,
            contributing_factors=factors,
        )
        return self.farm_repo.add_prediction(prediction)

    def generate_risk_alerts(self, farm_id: int, snapshot: FarmSnapshot) -> list[RiskAlert]:
        alerts: list[RiskAlert] = []
        if snapshot.drought_risk_score > 0.6:
            alerts.append(
                RiskAlert(
                    farm_id=farm_id,
                    alert_type='drought_warning',
                    severity='high',
                    message='High probability of drought in next 14 days.',
                    recommendation='Consider irrigation planning and water retention practices.',
                )
            )
        if snapshot.temperature_c > 36:
            alerts.append(
                RiskAlert(
                    farm_id=farm_id,
                    alert_type='heat_stress',
                    severity='medium',
                    message='Heat stress conditions detected for crop growth stage.',
                    recommendation='Apply heat mitigation through irrigation timing and mulching.',
                )
            )
        if snapshot.rainfall_mm < 15:
            alerts.append(
                RiskAlert(
                    farm_id=farm_id,
                    alert_type='weather_anomaly',
                    severity='medium',
                    message='Rainfall anomaly detected against seasonal baseline.',
                    recommendation='Adjust field operations and monitor short-term forecast changes.',
                )
            )
        return self.farm_repo.add_alerts(alerts) if alerts else []
