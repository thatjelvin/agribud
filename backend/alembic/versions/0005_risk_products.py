"""risk-products: credit / insurance / carbon tables

Revision ID: 0005_risk_products
Revises: 0004_vision
Create Date: 2026-06-02 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0005_risk_products"
down_revision = "0004_vision"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE TYPE credit_decision AS ENUM ('approved', 'declined', 'review')")
    op.execute("CREATE TYPE coverage_type AS ENUM ('drought', 'flood', 'multi_peril')")

    credit_decision_t = postgresql.ENUM(
        "approved",
        "declined",
        "review",
        name="credit_decision",
        create_type=False,
    )
    coverage_type_t = postgresql.ENUM(
        "drought",
        "flood",
        "multi_peril",
        name="coverage_type",
        create_type=False,
    )

    op.create_table(
        "credit_assessments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("farm_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("applicant_name", sa.String(length=255), nullable=False),
        sa.Column("requested_amount", sa.Float, nullable=False),
        sa.Column("approved_amount", sa.Float, nullable=True),
        sa.Column("risk_score", sa.Float, nullable=False),
        sa.Column("decision", credit_decision_t, nullable=False),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["farm_id"], ["farms.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_credit_assessments_farm_id", "credit_assessments", ["farm_id"])
    op.create_index(
        "ix_credit_assessments_decision", "credit_assessments", ["decision"]
    )

    op.create_table(
        "insurance_quotes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("farm_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("coverage_type", coverage_type_t, nullable=False),
        sa.Column("sum_insured", sa.Float, nullable=False),
        sa.Column("premium", sa.Float, nullable=False),
        sa.Column("valid_until", sa.Date, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["farm_id"], ["farms.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_insurance_quotes_farm_id", "insurance_quotes", ["farm_id"])

    op.create_table(
        "carbon_credits",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("farm_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("season", sa.String(length=120), nullable=False),
        sa.Column("tonnes_co2", sa.Float, nullable=False),
        sa.Column("methodology", sa.String(length=120), nullable=False),
        sa.Column("verified", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["farm_id"], ["farms.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_carbon_credits_farm_id", "carbon_credits", ["farm_id"])
    op.create_index("ix_carbon_credits_verified", "carbon_credits", ["verified"])


def downgrade() -> None:
    op.drop_index("ix_carbon_credits_verified", table_name="carbon_credits")
    op.drop_index("ix_carbon_credits_farm_id", table_name="carbon_credits")
    op.drop_table("carbon_credits")

    op.drop_index("ix_insurance_quotes_farm_id", table_name="insurance_quotes")
    op.drop_table("insurance_quotes")

    op.drop_index("ix_credit_assessments_decision", table_name="credit_assessments")
    op.drop_index("ix_credit_assessments_farm_id", table_name="credit_assessments")
    op.drop_table("credit_assessments")

    op.execute("DROP TYPE coverage_type")
    op.execute("DROP TYPE credit_decision")
