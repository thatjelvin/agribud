"""vision_diagnoses: computer-vision diagnosis table

Revision ID: 0004_vision
Revises: 0003_sensors
Create Date: 2026-06-02 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0004_vision"
down_revision = "0003_sensors"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "vision_diagnoses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("farm_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("image_hash", sa.String(length=64), nullable=False),
        sa.Column("diagnosis", sa.String(length=80), nullable=False),
        sa.Column("confidence", sa.Float, nullable=False),
        sa.Column("recommended_actions", sa.Text, nullable=False),
        sa.Column("model_version", sa.String(length=64), nullable=False),
        sa.Column("extra", postgresql.JSON, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["farm_id"], ["farms.id"], ondelete="SET NULL"),
    )
    op.create_index(
        "ix_vision_diagnoses_image_hash", "vision_diagnoses", ["image_hash"]
    )


def downgrade() -> None:
    op.drop_index("ix_vision_diagnoses_image_hash", table_name="vision_diagnoses")
    op.drop_table("vision_diagnoses")
