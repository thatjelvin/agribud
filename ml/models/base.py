from dataclasses import dataclass


@dataclass
class YieldPredictionResult:
    predicted_yield_ton_ha: float
    confidence_score: float
    contributing_factors: dict


class YieldModel:
    version: str = 'base'

    def predict(self, features: dict) -> YieldPredictionResult:  # pragma: no cover - interface
        raise NotImplementedError
