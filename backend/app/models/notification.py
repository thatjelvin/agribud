from __future__ import annotations

from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class NotificationKind(str, Enum):
    risk_created = "risk_created"
    yield_ready = "yield_ready"
    snapshot_low_ndvi = "snapshot_low_ndvi"
    system = "system"


class Notification(Base):
    """In-app notification (MVP: polling-based).

    Future iterations (per ARCHITECTURE §3.6) will fan these out via
    push/email/SMS/WhatsApp; the table is the canonical record.
    """

    __tablename__ = "notifications"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    kind: Mapped[NotificationKind] = mapped_column(
        SAEnum(NotificationKind, name="notification_kind"), index=True
    )
    title: Mapped[str] = mapped_column(String(255))
    body: Mapped[str] = mapped_column(Text)
    related_farm_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("farms.id"), nullable=True
    )
    related_risk_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("risks.id"), nullable=True
    )
    read: Mapped[bool] = mapped_column(default=False, index=True)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user = relationship("User", back_populates="notifications")
