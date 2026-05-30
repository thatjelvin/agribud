from ml.models.base import YieldModel, YieldPredictionResult


class StatisticalYieldModelV1(YieldModel):
    version = 'v1-statistical'

    def predict(self, features: dict) -> YieldPredictionResult:
        health = float(features.get('vegetation_health_score', 55.0))
        rainfall = float(features.get('rainfall_mm', 30.0))
        temperature = float(features.get('temperature_c', 30.0))
        predicted = max(0.5, 1.2 + (health / 100) * 3.5 + (rainfall / 100) - ((temperature - 30) * 0.08))
        confidence = min(0.95, 0.55 + health / 250)
        return YieldPredictionResult(
            predicted_yield_ton_ha=predicted,
            confidence_score=confidence,
            contributing_factors={
                'vegetation_health_score': health,
                'rainfall_mm': rainfall,
                'temperature_c': temperature,
            },
        )
