"""add immutable client report snapshots

Revision ID: a6c4e9d2f731
Revises: f5a8c9d1e240
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "a6c4e9d2f731"
down_revision: Union[str, Sequence[str], None] = "f5a8c9d1e240"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("client_reports",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("period_label", sa.String(120)),
        sa.Column("status", sa.String(20), server_default="draft", nullable=False),
        sa.Column("snapshot_version", sa.String(30), nullable=False),
        sa.Column("snapshot", sa.JSON(), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("share_token_hash", sa.String(64), unique=True),
        sa.Column("share_token_hint", sa.String(12)),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_client_reports_project_id", "client_reports", ["project_id"])
    op.create_index("ix_client_reports_status", "client_reports", ["status"])
    op.create_index("ix_client_reports_share_token_hash", "client_reports", ["share_token_hash"])


def downgrade() -> None:
    op.drop_table("client_reports")
