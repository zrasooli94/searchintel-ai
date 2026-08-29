"""add competitor discovery suggestions

Revision ID: b92f4d7e1a63
Revises: a6f4d9821c30
Create Date: 2026-08-29 14:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b92f4d7e1a63"
down_revision: Union[str, Sequence[str], None] = "a6f4d9821c30"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "competitor_discovery_suggestions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("brand_name", sa.String(length=255), nullable=False),
        sa.Column("normalized_name", sa.String(length=255), nullable=False),
        sa.Column("website_url", sa.String(length=2048), nullable=False),
        sa.Column("normalized_domain", sa.String(length=255), nullable=False),
        sa.Column("competitor_type", sa.String(length=30), nullable=False),
        sa.Column("confidence", sa.String(length=20), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("evidence", sa.JSON(), nullable=False),
        sa.Column("evidence_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("model_name", sa.String(length=255), nullable=True),
        sa.Column("approved_brand_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["approved_brand_id"], ["brands.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("project_id", "normalized_domain", name="uq_competitor_discovery_project_domain"),
    )
    op.create_index("ix_competitor_discovery_suggestions_project_id", "competitor_discovery_suggestions", ["project_id"])
    op.create_index("ix_competitor_discovery_suggestions_status", "competitor_discovery_suggestions", ["status"])


def downgrade() -> None:
    op.drop_index("ix_competitor_discovery_suggestions_status", table_name="competitor_discovery_suggestions")
    op.drop_index("ix_competitor_discovery_suggestions_project_id", table_name="competitor_discovery_suggestions")
    op.drop_table("competitor_discovery_suggestions")
