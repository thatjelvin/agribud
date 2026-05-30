from ml.features.feature_builder import build_features
from ml.models.statistical_v1 import StatisticalYieldModelV1


def predict(snapshot: dict, farm: dict) -> dict:
    model = StatisticalYieldModelV1()
    features = build_features(snapshot, farm)
    result = model.predict(features)
    return {
        'model_version': model.version,
        'predicted_yield_ton_ha': result.predicted_yield_ton_ha,
        'confidence_score': result.confidence_score,
        'contributing_factors': result.contributing_factors,
    }
