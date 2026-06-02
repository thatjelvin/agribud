from __future__ import annotations

import json
from uuid import UUID

from fastapi import HTTPException, status
from openai import OpenAI
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import Farm, Risk, Snapshot, Yield


def _error(detail: str, code: str) -> dict:
    return {"detail": detail, "code": code}


class CopilotService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def chat(
        self, message: str, farm_id: UUID | None
    ) -> tuple[str, list[str] | None]:
        """Send a copilot chat request with optional farm context.

        Returns (reply, sources). Sources are advisory hints about the
        data windows the reply was based on.
        """
        if not settings.openai_api_key:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail=_error(
                    "Copilot not configured. Set OPENAI_API_KEY in backend/.env.",
                    "COPILOT_NOT_CONFIGURED",
                ),
            )

        context: dict = {}
        sources: list[str] = []
        if farm_id:
            bundle = await self._load_farm_context(farm_id)
            if bundle:
                context = bundle["context"]
                sources = bundle["sources"]

        system_prompt = (
            "You are an expert agronomist and farm management advisor for the "
            "AgriPulse AI platform.\n"
            f"Farm data context: {json.dumps(context)}.\n"
            "Answer the farmer's question with specific, actionable advice. "
            "If the data is insufficient, say so explicitly rather than guessing."
        )

        client = OpenAI(
            api_key=settings.openai_api_key, base_url=settings.openai_base_url
        )
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message},
            ],
            temperature=0.3,
        )
        reply = response.choices[0].message.content or ""
        return reply, (sources or None)

    async def _load_farm_context(self, farm_id: UUID) -> dict | None:
        """Load farm, latest snapshot, latest yield, and open risks."""
        farm_result = await self.session.execute(select(Farm).where(Farm.id == farm_id))
        farm = farm_result.scalar_one_or_none()
        if not farm:
            return None

        snapshot_result = await self.session.execute(
            select(Snapshot)
            .where(Snapshot.farm_id == farm_id)
            .order_by(desc(Snapshot.captured_at))
            .limit(1)
        )
        snapshot = snapshot_result.scalar_one_or_none()

        yield_result = await self.session.execute(
            select(Yield)
            .where(Yield.farm_id == farm_id)
            .order_by(desc(Yield.created_at))
            .limit(1)
        )
        latest_yield = yield_result.scalar_one_or_none()

        risks_result = await self.session.execute(
            select(Risk).where(Risk.farm_id == farm_id, Risk.resolved.is_(False))
        )
        risks = [
            {
                "alert_type": risk.alert_type,
                "severity": risk.severity.value,
                "message": risk.message,
                "recommendation": risk.recommendation,
                "created_at": risk.created_at.isoformat(),
            }
            for risk in risks_result.scalars().all()
        ]

        context = {
            "farm": {
                "id": str(farm.id),
                "farm_name": farm.farm_name,
                "crop_type": farm.crop_type,
                "planting_date": farm.planting_date.isoformat(),
                "expected_harvest_date": farm.expected_harvest_date.isoformat(),
                "farm_size_ha": farm.farm_size_ha,
            },
            "latest_snapshot": None,
            "latest_yield_prediction": None,
            "open_risks": risks,
        }
        sources: list[str] = []
        if snapshot:
            context["latest_snapshot"] = {
                "captured_at": snapshot.captured_at.isoformat(),
                "ndvi": snapshot.ndvi,
                "vegetation_health_score": snapshot.vegetation_health_score,
                "rainfall_mm": snapshot.rainfall_mm,
                "temperature_c": snapshot.temperature_c,
                "drought_risk_score": snapshot.drought_risk_score,
                "source": snapshot.source,
            }
            sources.append(
                f"snapshot@{snapshot.captured_at.isoformat()} ({snapshot.source})"
            )
        if latest_yield:
            context["latest_yield_prediction"] = {
                "season": latest_yield.season,
                "predicted_yield_ton_ha": latest_yield.predicted_yield_ton_ha,
                "confidence_score": latest_yield.confidence_score,
                "model_version": latest_yield.model_version,
                "created_at": latest_yield.created_at.isoformat(),
            }
            sources.append(
                f"yield@{latest_yield.created_at.isoformat()} ({latest_yield.model_version})"
            )
        return {"context": context, "sources": sources}
