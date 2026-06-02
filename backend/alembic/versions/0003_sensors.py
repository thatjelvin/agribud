"""sensor_readings: IoT sensor ingestion table

Revision ID: 0003_sensors
Revises: 0002_notifications
Create Date: 2026-06-02 00:00:00

MVP schema for the IoT ingestion endpoint. The production design
(per ARCHITECTURE §3.5) will route MQTT/LoRaWAN payloads into a
time-series store, but the SQLAlchemy model here is the canonical
record for the MVP HTTP path.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0003_sensors"
down_revision = "0002_notifications"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sensor_readings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("farm_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sensor_type", sa.String(length=64), nullable=False),
        sa.Column("value", sa.Float, nullable=False),
        sa.Column("unit", sa.String(length=32), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("extra", postgresql.JSON, nullable=True),
        sa.Column(
            "received_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["farm_id"], ["farms.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_sensor_readings_farm_id", "sensor_readings", ["farm_id"])
    op.create_index(
        "ix_sensor_readings_sensor_type", "sensor_readings", ["sensor_type"]
    )
    op.create_index(
        "ix_sensor_readings_recorded_at", "sensor_readings", ["recorded_at"]
    )


def downgrade() -> None:
    op.drop_index("ix_sensor_readings_recorded_at", table_name="sensor_readings")
    op.drop_index("ix_sensor_readings_sensor_type", table_name="sensor_readings")
    op.drop_index("ix_sensor_readings_farm_id", table_name="sensor_readings")
    op.drop_table("sensor_readings")
