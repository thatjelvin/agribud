"""notifications: in-app notification table

Revision ID: 0002_notifications
Revises: 0001_initial
Create Date: 2026-06-02 00:00:00

Adds the ``notifications`` table + ``notification_kind`` enum type. Wires
up FKs to ``users``, ``farms``, ``risks`` with ON DELETE CASCADE matching
the SQLAlchemy ``cascade="all, delete-orphan"`` relationships.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002_notifications"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "CREATE TYPE notification_kind AS ENUM "
        "('risk_created', 'yield_ready', 'snapshot_low_ndvi', 'system')"
    )

    notification_kind_t = postgresql.ENUM(
        "risk_created",
        "yield_ready",
        "snapshot_low_ndvi",
        "system",
        name="notification_kind",
        create_type=False,
    )
    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("kind", notification_kind_t, nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("related_farm_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("related_risk_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("read", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["related_farm_id"], ["farms.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["related_risk_id"], ["risks.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])
    op.create_index("ix_notifications_kind", "notifications", ["kind"])
    op.create_index("ix_notifications_read", "notifications", ["read"])


def downgrade() -> None:
    op.drop_index("ix_notifications_read", table_name="notifications")
    op.drop_index("ix_notifications_kind", table_name="notifications")
    op.drop_index("ix_notifications_user_id", table_name="notifications")
    op.drop_table("notifications")
    op.execute("DROP TYPE notification_kind")
