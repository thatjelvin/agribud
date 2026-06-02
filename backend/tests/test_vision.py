"""F12 computer-vision diagnosis MVP scaffold tests."""

from __future__ import annotations

from app.models.vision import diagnose_from_hash


def test_diagnose_from_hash_is_deterministic():
    a = diagnose_from_hash("test-image-1")
    b = diagnose_from_hash("test-image-1")
    assert a == b


def test_diagnose_from_hash_returns_valid_confidence():
    diagnosis, confidence, message, action = diagnose_from_hash("any-string")
    assert diagnosis
    assert 0.0 < confidence <= 1.0
    assert message
    assert action


def test_openapi_exposes_vision_diagnose():
    from app.main import app

    spec = app.openapi()
    assert "/api/v1/vision/diagnose" in spec["paths"]
    assert "post" in spec["paths"]["/api/v1/vision/diagnose"]


def test_vision_request_rejects_oversized_url():
    from pydantic import ValidationError

    from app.schemas.vision import VisionDiagnoseRequest

    with pytest.raises(ValidationError):
        VisionDiagnoseRequest(image_url="https://x.com/" + "a" * 2100)


import pytest
