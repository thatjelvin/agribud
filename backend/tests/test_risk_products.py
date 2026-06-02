"""F14 risk-products MVP scaffold tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.routers.risk_products import _credit_decision
from app.models.risk_products import CreditDecision


def test_credit_decision_rules():
    assert _credit_decision(0.1, 1000) == (CreditDecision.approved, 1000)
    assert _credit_decision(0.4, 1000)[0] == CreditDecision.approved
    assert _credit_decision(0.4, 1000)[1] == 600.0
    assert _credit_decision(0.7, 1000)[0] == CreditDecision.review
    assert _credit_decision(0.9, 1000) == (CreditDecision.declined, None)


def test_credit_assessment_create_rejects_oversized_amount():
    from app.schemas.risk_products import CreditAssessmentCreate

    with pytest.raises(ValidationError):
        CreditAssessmentCreate(
            farm_id="00000000-0000-0000-0000-000000000000",
            applicant_name="Jane",
            requested_amount=20_000_000,
            risk_score=0.2,
        )


def test_credit_assessment_create_rejects_risk_out_of_range():
    from app.schemas.risk_products import CreditAssessmentCreate

    with pytest.raises(ValidationError):
        CreditAssessmentCreate(
            farm_id="00000000-0000-0000-0000-000000000000",
            applicant_name="Jane",
            requested_amount=1000,
            risk_score=1.5,
        )


def test_openapi_exposes_risk_products():
    from app.main import app

    spec = app.openapi()
    paths = spec["paths"]
    for endpoint in (
        "/api/v1/risk-products/credit-assessments",
        "/api/v1/risk-products/insurance-quotes",
        "/api/v1/risk-products/carbon-credits",
    ):
        assert endpoint in paths
        assert "get" in paths[endpoint]
        assert "post" in paths[endpoint]


def test_carbon_credit_validates_tonnes():
    from app.schemas.risk_products import CarbonCreditCreate

    good = CarbonCreditCreate(
        farm_id="00000000-0000-0000-0000-000000000000",
        season="2024",
        tonnes_co2=12.5,
        methodology="VM0042",
    )
    assert good.tonnes_co2 == 12.5

    with pytest.raises(ValidationError):
        CarbonCreditCreate(
            farm_id="00000000-0000-0000-0000-000000000000",
            season="2024",
            tonnes_co2=20_000,
            methodology="VM0042",
        )
