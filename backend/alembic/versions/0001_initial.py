"""initial schema: users, farms, snapshots, yields, risks

Revision ID: 0001_initial
Revises:
Create Date: 2026-06-01 00:00:00

Brings the database to the schema defined by app/models/*.
Includes PostGIS extension, enums for user_role and risk_severity,
the UUID-keyed tables, indexes, and FK constraints.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from geoalchemy2 import Geometry
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    # Create Postgres enum types via raw DDL. The Enum column metadata
    # below uses create_type=False to prevent Alembic from re-emitting
    # CREATE TYPE when the tables are built.
    op.execute(
        "CREATE TYPE user_role AS ENUM "
        "('farmer', 'agribusiness', 'financial_institution', 'admin')"
    )
    op.execute(
        "CREATE TYPE risk_severity AS ENUM ('low', 'medium', 'high', 'critical')"
    )

    user_role_t = postgresql.ENUM(
        "farmer",
        "agribusiness",
        "financial_institution",
        "admin",
        name="user_role",
        create_type=False,
    )
    risk_severity_t = postgresql.ENUM(
        "low",
        "medium",
        "high",
        "critical",
        name="risk_severity",
        create_type=False,
    )

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("role", user_role_t, nullable=False, server_default="farmer"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "farms",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "owner_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("farm_name", sa.String(255), nullable=False),
        sa.Column("crop_type", sa.String(120), nullable=False),
        sa.Column("planting_date", sa.Date, nullable=False),
        sa.Column("expected_harvest_date", sa.Date, nullable=False),
        sa.Column("farm_size_ha", sa.Float, nullable=False),
        sa.Column("polygon_geojson", sa.JSON, nullable=False),
        sa.Column(
            "boundary",
            Geometry(geometry_type="POLYGON", srid=4326),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_farms_owner_id", "farms", ["owner_id"])
    op.create_index("ix_farms_farm_name", "farms", ["farm_name"])

    op.create_table(
        "snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "farm_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("farms.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "source", sa.String(64), nullable=False, server_default="sentinel_nasa"
        ),
        sa.Column("ndvi", sa.Float, nullable=False),
        sa.Column("vegetation_health_score", sa.Float, nullable=False),
        sa.Column("rainfall_mm", sa.Float, nullable=False),
        sa.Column("temperature_c", sa.Float, nullable=False),
        sa.Column("drought_risk_score", sa.Float, nullable=False),
        sa.Column("soil_moisture", sa.Float, nullable=True),
        sa.Column("image_url", sa.String(512), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column(
            "captured_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_snapshots_farm_id", "snapshots", ["farm_id"])
    op.create_index("ix_snapshots_captured_at", "snapshots", ["captured_at"])

    op.create_table(
        "yields",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "farm_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("farms.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("season", sa.String(120), nullable=False),
        sa.Column("predicted_yield_ton_ha", sa.Float, nullable=True),
        sa.Column("confidence_score", sa.Float, nullable=True),
        sa.Column("contributing_factors", sa.JSON, nullable=True),
        sa.Column("actual_kg_ha", sa.Float, nullable=True),
        sa.Column(
            "model_version",
            sa.String(64),
            nullable=False,
            server_default="v1-statistical",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_yields_farm_id", "yields", ["farm_id"])

    op.create_table(
        "risks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "farm_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("farms.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("alert_type", sa.String(80), nullable=False),
        sa.Column("severity", risk_severity_t, nullable=False),
        sa.Column("message", sa.Text, nullable=False),
        sa.Column("recommendation", sa.Text, nullable=False),
        sa.Column("resolved", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_risks_farm_id", "risks", ["farm_id"])
    op.create_index("ix_risks_alert_type", "risks", ["alert_type"])
    op.create_index("ix_risks_severity", "risks", ["severity"])


def downgrade() -> None:
    op.drop_index("ix_risks_severity", table_name="risks")
    op.drop_index("ix_risks_alert_type", table_name="risks")
    op.drop_index("ix_risks_farm_id", table_name="risks")
    op.drop_table("risks")

    op.drop_index("ix_yields_farm_id", table_name="yields")
    op.drop_table("yields")

    op.drop_index("ix_snapshots_captured_at", table_name="snapshots")
    op.drop_index("ix_snapshots_farm_id", table_name="snapshots")
    op.drop_table("snapshots")

    op.drop_index("ix_farms_farm_name", table_name="farms")
    op.drop_index("ix_farms_owner_id", table_name="farms")
    op.drop_table("farms")

    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")

    op.execute("DROP TYPE IF EXISTS risk_severity")
    op.execute("DROP TYPE IF EXISTS user_role")
