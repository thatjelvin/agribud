from app.application.services.analytics_service import AnalyticsService


def test_prediction_formula_is_positive():
    class Repo:
        def add_prediction(self, prediction):
            return prediction

    class Farm:
        id = 1
        crop_type = 'Maize'

    class Snapshot:
        vegetation_health_score = 75
        rainfall_mm = 40
        temperature_c = 31

    service = AnalyticsService(Repo(), geospatial_provider=None)  # type: ignore[arg-type]
    result = service.predict_yield(Farm(), Snapshot())

    assert result.predicted_yield_ton_ha > 0
    assert 0 <= result.confidence_score <= 1
