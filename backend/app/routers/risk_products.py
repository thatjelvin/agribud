from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models import (
    CarbonCredit,
    CreditAssessment,
    CreditDecision,
    Farm,
    InsuranceQuote,
    User,
)
from app.schemas.common import Page
from app.schemas.risk_products import (
    CarbonCreditCreate,
    CarbonCreditOut,
    CreditAssessmentCreate,
    CreditAssessmentOut,
    InsuranceQuoteCreate,
    InsuranceQuoteOut,
)
from app.services.farm_service import FarmService
from app.utils.dependencies import get_current_user, require_role

router = APIRouter(prefix="/risk-products", tags=["risk-products"])


def _error(detail: str, code: str) -> dict:
    return {"detail": detail, "code": code}


async def _resolve_farm(
    session: AsyncSession, farm_id: UUID, current_user: User
) -> Farm:
    farm_service = FarmService(session)
    return await farm_service.get_farm_for_owner(farm_id, current_user.id)


def _credit_decision(
    risk_score: float, requested: float
) -> tuple[CreditDecision, float | None]:
    if risk_score < 0.3:
        return CreditDecision.approved, requested
    if risk_score < 0.6:
        return CreditDecision.approved, round(requested * 0.6, 2)
    if risk_score < 0.8:
        return CreditDecision.review, None
    return CreditDecision.declined, None


@router.post(
    "/credit-assessments",
    response_model=CreditAssessmentOut,
    status_code=201,
)
async def create_credit_assessment(
    payload: CreditAssessmentCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> CreditAssessmentOut:
    await _resolve_farm(session, payload.farm_id, current_user)
    decision, approved = _credit_decision(payload.risk_score, payload.requested_amount)
    entry = CreditAssessment(
        farm_id=payload.farm_id,
        applicant_name=payload.applicant_name,
        requested_amount=payload.requested_amount,
        approved_amount=approved,
        risk_score=payload.risk_score,
        decision=decision,
        notes=payload.notes,
    )
    session.add(entry)
    await session.commit()
    await session.refresh(entry)
    return CreditAssessmentOut.model_validate(entry)


@router.get(
    "/credit-assessments",
    response_model=Page[CreditAssessmentOut],
)
async def list_credit_assessments(
    decision: CreditDecision | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
    _: User = Depends(require_role("financial_institution", "admin")),
) -> Page[CreditAssessmentOut]:
    where = []
    if decision is not None:
        where.append(CreditAssessment.decision == decision)
    total = (
        await session.execute(
            select(func.count()).select_from(CreditAssessment).where(*where)
        )
    ).scalar_one()
    items = list(
        (
            await session.execute(
                select(CreditAssessment)
                .where(*where)
                .order_by(desc(CreditAssessment.created_at))
                .limit(limit)
                .offset(offset)
            )
        )
        .scalars()
        .all()
    )
    return Page[CreditAssessmentOut](
        items=[CreditAssessmentOut.model_validate(i) for i in items],
        total=int(total),
        limit=limit,
        offset=offset,
    )


@router.post("/insurance-quotes", response_model=InsuranceQuoteOut, status_code=201)
async def create_insurance_quote(
    payload: InsuranceQuoteCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> InsuranceQuoteOut:
    await _resolve_farm(session, payload.farm_id, current_user)
    entry = InsuranceQuote(
        farm_id=payload.farm_id,
        coverage_type=payload.coverage_type,
        sum_insured=payload.sum_insured,
        premium=payload.premium,
        valid_until=payload.valid_until,
    )
    session.add(entry)
    await session.commit()
    await session.refresh(entry)
    return InsuranceQuoteOut.model_validate(entry)


@router.get("/insurance-quotes", response_model=Page[InsuranceQuoteOut])
async def list_insurance_quotes(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
    _: User = Depends(require_role("financial_institution", "admin")),
) -> Page[InsuranceQuoteOut]:
    total = await session.scalar(select(func.count(InsuranceQuote.id))) or 0
    items = list(
        (
            await session.execute(
                select(InsuranceQuote)
                .order_by(desc(InsuranceQuote.created_at))
                .limit(limit)
                .offset(offset)
            )
        )
        .scalars()
        .all()
    )
    return Page[InsuranceQuoteOut](
        items=[InsuranceQuoteOut.model_validate(i) for i in items],
        total=int(total),
        limit=limit,
        offset=offset,
    )


@router.post("/carbon-credits", response_model=CarbonCreditOut, status_code=201)
async def create_carbon_credit(
    payload: CarbonCreditCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> CarbonCreditOut:
    await _resolve_farm(session, payload.farm_id, current_user)
    entry = CarbonCredit(
        farm_id=payload.farm_id,
        season=payload.season,
        tonnes_co2=payload.tonnes_co2,
        methodology=payload.methodology,
        verified=payload.verified,
    )
    session.add(entry)
    await session.commit()
    await session.refresh(entry)
    return CarbonCreditOut.model_validate(entry)


@router.get("/carbon-credits", response_model=Page[CarbonCreditOut])
async def list_carbon_credits(
    verified: bool | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
    _: User = Depends(require_role("agribusiness", "financial_institution", "admin")),
) -> Page[CarbonCreditOut]:
    where = []
    if verified is not None:
        where.append(CarbonCredit.verified.is_(verified))
    total = (
        await session.execute(
            select(func.count()).select_from(CarbonCredit).where(*where)
        )
    ).scalar_one()
    items = list(
        (
            await session.execute(
                select(CarbonCredit)
                .where(*where)
                .order_by(desc(CarbonCredit.created_at))
                .limit(limit)
                .offset(offset)
            )
        )
        .scalars()
        .all()
    )
    return Page[CarbonCreditOut](
        items=[CarbonCreditOut.model_validate(i) for i in items],
        total=int(total),
        limit=limit,
        offset=offset,
    )
