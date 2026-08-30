"""add project priority center

Revision ID: f5a8c9d1e240
Revises: e4b7c1d2a930
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "f5a8c9d1e240"
down_revision: Union[str, Sequence[str], None] = "e4b7c1d2a930"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "project_priorities",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("stable_key", sa.String(255), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("priority", sa.String(20), nullable=False),
        sa.Column("priority_score", sa.Integer(), nullable=False),
        sa.Column("impact", sa.String(20), nullable=False),
        sa.Column("effort", sa.String(20), nullable=False),
        sa.Column("confidence", sa.String(20), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="open"),
        sa.Column("observed_evidence", sa.JSON(), nullable=False),
        sa.Column("interpretation", sa.Text(), nullable=False),
        sa.Column("recommended_action", sa.Text(), nullable=False),
        sa.Column("affected_prompts", sa.JSON(), nullable=False),
        sa.Column("affected_pages", sa.JSON(), nullable=False),
        sa.Column("affected_entities", sa.JSON(), nullable=False),
        sa.Column("source_modes", sa.JSON(), nullable=False),
        sa.Column("score_components", sa.JSON(), nullable=False),
        sa.Column("provenance", sa.JSON(), nullable=False),
        sa.Column("evidence_fingerprint", sa.String(64), nullable=False),
        sa.Column("is_resolved", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("project_id", "stable_key", name="uq_project_priority_stable_key"),
    )
    op.create_index("ix_project_priorities_project_id", "project_priorities", ["project_id"])
    op.create_index("ix_project_priorities_priority", "project_priorities", ["priority"])
    op.create_index("ix_project_priorities_priority_score", "project_priorities", ["priority_score"])
    op.create_index("ix_project_priorities_status", "project_priorities", ["status"])
    op.create_index("ix_project_priorities_is_resolved", "project_priorities", ["is_resolved"])


def downgrade() -> None:
    op.drop_table("project_priorities")
