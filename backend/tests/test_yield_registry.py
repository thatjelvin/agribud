"""Yield model registry + F5 swappability contract."""

from __future__ import annotations

import pytest

from ml.models.registry import (
    DEFAULT_VERSION,
    get_active,
    get_default_for_env,
    list_versions,
    register,
    resolve,
)
from ml.models.stub_v0 import DeterministicStubYieldModelV0


def test_default_version_is_registered():
    assert DEFAULT_VERSION in [v["name"] for v in list_versions()]


def test_get_active_returns_default_when_version_omitted():
    model = get_active()
    assert model.version == DEFAULT_VERSION


def test_get_active_with_explicit_version():
    register("v0-stub", DeterministicStubYieldModelV0)
    model = get_active("v0-stub")
    assert isinstance(model, DeterministicStubYieldModelV0)
    assert model.version == "v0-stub"


def test_resolve_unknown_raises_keyerror():
    with pytest.raises(KeyError):
        resolve("nonexistent-model-xyz")


def test_register_rejects_non_yield_model_subclasses():
    class NotAModel:
        pass

    with pytest.raises(TypeError):
        register("nope", NotAModel)


def test_list_versions_includes_module_and_class():
    versions = list_versions()
    assert versions, "registry should have at least the default"
    for entry in versions:
        assert "name" in entry
        assert "module" in entry
        assert "class" in entry


def test_get_default_for_env_with_registered_name():
    register("v0-stub", DeterministicStubYieldModelV0)
    model = get_default_for_env("v0-stub")
    assert isinstance(model, DeterministicStubYieldModelV0)


def test_get_default_for_env_falls_back_to_default():
    model = get_default_for_env("does-not-exist")
    assert model.version == DEFAULT_VERSION


def test_get_default_for_env_with_module_path():
    model = get_default_for_env("ml.models.stub_v0:DeterministicStubYieldModelV0")
    assert model.version == "v0-stub"


def test_get_default_for_env_with_none_returns_default():
    model = get_default_for_env(None)
    assert model.version == DEFAULT_VERSION


def test_predict_uses_registry_version(monkeypatch):
    from ml.inference import realtime

    register("v0-stub", DeterministicStubYieldModelV0)
    result = realtime.predict(
        {
            "ndvi": 0.5,
            "vegetation_health_score": 50,
            "rainfall_mm": 30,
            "temperature_c": 25,
        },
        {"farm_size_ha": 1.0, "crop_type": "Maize"},
        version="v0-stub",
    )
    assert result["model_version"] == "v0-stub"
    assert result["predicted_yield_ton_ha"] == 3.0


def test_predict_default_model_is_v1_statistical():
    from ml.inference import realtime

    result = realtime.predict(
        {
            "ndvi": 0.5,
            "vegetation_health_score": 50,
            "rainfall_mm": 30,
            "temperature_c": 25,
        },
        {"farm_size_ha": 1.0, "crop_type": "Maize"},
    )
    assert result["model_version"] == "v1-statistical"
