from __future__ import annotations

import asyncio
from uuid import UUID

from sqlalchemy import desc, select

from app.database import SessionLocal
from app.models import Risk, RiskSeverity, Snapshot
from app.tasks.celery_app import celery_app


@celery_app.task
def run_risk_assessment(farm_id: str) -> str:
    """Evaluate the latest snapshot and create Risk alerts with PRD-shaped fields.

    Thresholds (MVP heuristic, mock-data driven):
      - drought_risk_score >= 0.6  -> high   "drought_warning"
      - temperature_c      >  36   -> medium "heat_stress"
      - rainfall_mm        <  15   -> medium "weather_anomaly"
    """

    async def _run() -> None:
        async with SessionLocal() as session:
            farm_uuid = UUID(farm_id)
            result = await session.execute(
                select(Snapshot)
                .where(Snapshot.farm_id == farm_uuid)
                .order_by(desc(Snapshot.captured_at))
                .limit(1)
            )
            snapshot = result.scalar_one_or_none()
            if not snapshot:
                return

            alerts: list[Risk] = []
            if snapshot.drought_risk_score >= 0.6:
                alerts.append(
                    Risk(
                        farm_id=farm_uuid,
                        alert_type="drought_warning",
                        severity=RiskSeverity.high,
                        message="High probability of drought in the next 14 days.",
                        recommendation=(
                            "Prioritize irrigation planning, soil moisture monitoring, "
                            "and water retention practices this week."
                        ),
                    )
                )
            if snapshot.temperature_c > 36.0:
                alerts.append(
                    Risk(
                        farm_id=farm_uuid,
                        alert_type="heat_stress",
                        severity=RiskSeverity.medium,
                        message="Heat stress conditions detected for the current growth stage.",
                        recommendation=(
                            "Adjust irrigation timing to cooler hours and apply mulching "
                            "to reduce soil temperature."
                        ),
                    )
                )
            if snapshot.rainfall_mm < 15.0:
                alerts.append(
                    Risk(
                        farm_id=farm_uuid,
                        alert_type="weather_anomaly",
                        severity=RiskSeverity.medium,
                        message="Rainfall anomaly detected against seasonal baseline.",
                        recommendation=(
                            "Replan field operations and monitor the short-term forecast "
                            "for the next 7 days."
                        ),
                    )
                )

            if alerts:
                session.add_all(alerts)
                await session.commit()
                from app.services.notification_service import notify_risk_created

                for alert in alerts:
                    await notify_risk_created(session, alert)

    asyncio.run(_run())
    return "risk_assessment_complete"
