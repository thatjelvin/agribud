from __future__ import annotations

from uuid import UUID

from sqlalchemy import desc, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Notification, NotificationKind, Risk, User
from app.models.farm import Farm


class NotificationService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        user_id: UUID,
        kind: NotificationKind,
        title: str,
        body: str,
        *,
        related_farm_id: UUID | None = None,
        related_risk_id: UUID | None = None,
    ) -> Notification:
        entry = Notification(
            user_id=user_id,
            kind=kind,
            title=title,
            body=body,
            related_farm_id=related_farm_id,
            related_risk_id=related_risk_id,
        )
        self.session.add(entry)
        await self.session.commit()
        await self.session.refresh(entry)
        return entry

    async def list_for_user(
        self, user_id: UUID, *, limit: int, offset: int, unread_only: bool = False
    ) -> tuple[list[Notification], int]:
        where = [Notification.user_id == user_id]
        if unread_only:
            where.append(Notification.read.is_(False))
        total = (
            await self.session.execute(
                select(func.count()).select_from(Notification).where(*where)
            )
        ).scalar_one()
        items = list(
            (
                await self.session.execute(
                    select(Notification)
                    .where(*where)
                    .order_by(desc(Notification.created_at))
                    .limit(limit)
                    .offset(offset)
                )
            )
            .scalars()
            .all()
        )
        return items, int(total)

    async def unread_count(self, user_id: UUID) -> int:
        return int(
            (
                await self.session.execute(
                    select(func.count())
                    .select_from(Notification)
                    .where(
                        Notification.user_id == user_id, Notification.read.is_(False)
                    )
                )
            ).scalar_one()
        )

    async def mark_read(self, user_id: UUID, notification_id: UUID) -> bool:
        result = await self.session.execute(
            update(Notification)
            .where(Notification.id == notification_id, Notification.user_id == user_id)
            .values(read=True)
            .returning(Notification.id)
        )
        await self.session.commit()
        return result.scalar_one_or_none() is not None

    async def mark_all_read(self, user_id: UUID) -> int:
        result = await self.session.execute(
            update(Notification)
            .where(Notification.user_id == user_id, Notification.read.is_(False))
            .values(read=True)
            .returning(Notification.id)
        )
        await self.session.commit()
        return len(result.scalars().all())


async def notify_risk_created(session: AsyncSession, risk: Risk) -> Notification | None:
    """Fan out a notification to the farm owner when a new risk is created."""
    farm = await session.get(Farm, risk.farm_id)
    if farm is None:
        return None
    owner = await session.get(User, farm.owner_id)
    if owner is None:
        return None
    service = NotificationService(session)
    return await service.create(
        user_id=owner.id,
        kind=NotificationKind.risk_created,
        title=f"New {risk.alert_type.replace('_', ' ')} alert ({risk.severity.value})",
        body=f"{risk.message} Recommendation: {risk.recommendation}",
        related_farm_id=risk.farm_id,
        related_risk_id=risk.id,
    )
