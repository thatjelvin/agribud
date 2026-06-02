"""Realtime inference entry point. The active model is selected by the
:class:`YieldModelRegistry`; the caller does not have to know which
implementation is in use.
"""

from __future__ import annotations

from ml.features.feature_builder import build_features
from ml.models.registry import get_default_for_env


def predict(
    snapshot: dict,
    farm: dict,
    *,
    version: str | None = None,
    env_model: str | None = None,
) -> dict:
    """Run the active yield model and return a JSON-shaped result.

    Args:
        snapshot: the latest snapshot dict (or None).
        farm: farm metadata (size, crop type).
        version: explicit model version override; wins over env_model.
        env_model: env-var value (name or ``module:Class``).
    """
    if version is not None:
        from ml.models.registry import get_active

        model = get_active(version)
    else:
        model = get_default_for_env(env_model)
    features = build_features(snapshot, farm)
    result = model.predict(features)
    return {
        "model_version": model.version,
        "predicted_yield_ton_ha": result.predicted_yield_ton_ha,
        "confidence_score": result.confidence_score,
        "contributing_factors": result.contributing_factors,
    }
