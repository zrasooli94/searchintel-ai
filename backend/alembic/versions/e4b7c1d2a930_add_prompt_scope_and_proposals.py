"""add prompt scope and proposals

Revision ID: e4b7c1d2a930
Revises: b92f4d7e1a63
Create Date: 2026-08-29 18:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e4b7c1d2a930"
down_revision: Union[str, Sequence[str], None] = "b92f4d7e1a63"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("projects", sa.Column(
        "measurement_scope", sa.String(length=20), nullable=False,
        server_default="brand_wide",
    ))
    op.add_column("projects", sa.Column(
        "measurement_focus", sa.String(length=255), nullable=True,
    ))
    op.create_table(
        "prompt_set_proposals",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="proposed"),
        sa.Column("generator_version", sa.String(length=50), nullable=False),
        sa.Column("measurement_scope", sa.String(length=20), nullable=False),
        sa.Column("focus_label", sa.String(length=255), nullable=True),
        sa.Column("source_website_id", sa.Integer(), nullable=True),
        sa.Column("source_page_count", sa.Integer(), nullable=False),
        sa.Column("model_name", sa.String(length=255), nullable=False),
        sa.Column("topic_clusters", sa.JSON(), nullable=False),
        sa.Column("coverage_blueprint", sa.JSON(), nullable=False),
        sa.Column("prompts", sa.JSON(), nullable=False),
        sa.Column("warnings", sa.JSON(), nullable=False),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_website_id"], ["websites.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_prompt_set_proposals_project_id", "prompt_set_proposals", ["project_id"])
    op.create_index("ix_prompt_set_proposals_status", "prompt_set_proposals", ["status"])


def downgrade() -> None:
    op.drop_index("ix_prompt_set_proposals_status", table_name="prompt_set_proposals")
    op.drop_index("ix_prompt_set_proposals_project_id", table_name="prompt_set_proposals")
    op.drop_table("prompt_set_proposals")
    op.drop_column("projects", "measurement_focus")
    op.drop_column("projects", "measurement_scope")
