"""Tests for the StatisticalYieldModelV1 formula.

Targets the actual ML module under ml/, not the old clean-arch service.
"""

from __future__ import annotations

import math

import pytest

from ml.inference.realtime import predict
from ml.models.statistical_v1 import StatisticalYieldModelV1


FARM = {"farm_size_ha": 2.5, "crop_type": "maize"}


def test_predict_returns_required_keys():
    snapshot = {
        "ndvi": 0.65,
        "vegetation_health_score": 70.0,
        "rainfall_mm": 45.0,
        "temperature_c": 28.0,
    }
    result = predict(snapshot, FARM)
    assert result["model_version"] == "v1-statistical"
    assert "predicted_yield_ton_ha" in result
    assert "confidence_score" in result
    assert "contributing_factors" in result


def test_predict_yield_is_positive():
    snapshot = {
        "ndvi": 0.7,
        "vegetation_health_score": 75.0,
        "rainfall_mm": 40.0,
        "temperature_c": 31.0,
    }
    result = predict(snapshot, FARM)
    assert result["predicted_yield_ton_ha"] > 0
    assert 0.0 <= result["confidence_score"] <= 0.95


def test_predict_higher_health_yields_higher_production():
    low = predict(
        {
            "ndvi": 0.2,
            "vegetation_health_score": 20.0,
            "rainfall_mm": 30.0,
            "temperature_c": 30.0,
        },
        FARM,
    )
    high = predict(
        {
            "ndvi": 0.9,
            "vegetation_health_score": 95.0,
            "rainfall_mm": 80.0,
            "temperature_c": 25.0,
        },
        FARM,
    )
    assert high["predicted_yield_ton_ha"] > low["predicted_yield_ton_ha"]


def test_predict_extreme_heat_penalizes_yield():
    cool = predict(
        {
            "ndvi": 0.7,
            "vegetation_health_score": 70.0,
            "rainfall_mm": 50.0,
            "temperature_c": 22.0,
        },
        FARM,
    )
    hot = predict(
        {
            "ndvi": 0.7,
            "vegetation_health_score": 70.0,
            "rainfall_mm": 50.0,
            "temperature_c": 38.0,
        },
        FARM,
    )
    assert hot["predicted_yield_ton_ha"] < cool["predicted_yield_ton_ha"]


def test_model_version_is_v1_statistical():
    model = StatisticalYieldModelV1()
    assert model.version == "v1-statistical"


def test_contributing_factors_includes_inputs():
    snapshot = {
        "ndvi": 0.55,
        "vegetation_health_score": 60.0,
        "rainfall_mm": 35.0,
        "temperature_c": 29.0,
    }
    result = predict(snapshot, FARM)
    factors = result["contributing_factors"]
    assert factors["vegetation_health_score"] == 60.0
    assert factors["rainfall_mm"] == 35.0
    assert factors["temperature_c"] == 29.0
