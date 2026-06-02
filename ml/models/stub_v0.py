"""Trivial stub yield model. Used for tests and as a placeholder while a
real model is trained. Returns a fixed prediction regardless of features.
"""

from __future__ import annotations

from ml.models.base import YieldModel, YieldPredictionResult


class DeterministicStubYieldModelV0(YieldModel):
    version = "v0-stub"

    def __init__(self, predicted: float = 3.0, confidence: float = 0.5):
        self._predicted = predicted
        self._confidence = confidence

    def predict(self, features: dict) -> YieldPredictionResult:
        return YieldPredictionResult(
            predicted_yield_ton_ha=self._predicted,
            confidence_score=self._confidence,
            contributing_factors={"stub": True},
        )
