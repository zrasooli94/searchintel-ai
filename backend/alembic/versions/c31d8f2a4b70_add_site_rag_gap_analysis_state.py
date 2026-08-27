"""add site rag gap analysis state

Revision ID: c31d8f2a4b70
Revises: e60ffab4e9c6
Create Date: 2026-08-27 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c31d8f2a4b70"
down_revision: Union[str, Sequence[str], None] = "e60ffab4e9c6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "site_rag_gap_analyses",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("experiment_id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("target_brand_id", sa.Integer(), nullable=False),
        sa.Column("gap_version", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("total_prompts", sa.Integer(), nullable=True),
        sa.Column("gap_count", sa.Integer(), nullable=False),
        sa.Column(
            "refreshed_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["experiment_id"],
            ["geo_experiments.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["target_brand_id"],
            ["brands.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "experiment_id",
            name="uq_site_rag_gap_analysis_experiment",
        ),
    )
    op.create_index(
        op.f("ix_site_rag_gap_analyses_experiment_id"),
        "site_rag_gap_analyses",
        ["experiment_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_site_rag_gap_analyses_project_id"),
        "site_rag_gap_analyses",
        ["project_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_site_rag_gap_analyses_refreshed_at"),
        "site_rag_gap_analyses",
        ["refreshed_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_site_rag_gap_analyses_status"),
        "site_rag_gap_analyses",
        ["status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_site_rag_gap_analyses_target_brand_id"),
        "site_rag_gap_analyses",
        ["target_brand_id"],
        unique=False,
    )

    op.execute(
        """
        INSERT INTO site_rag_gap_analyses (
            experiment_id,
            project_id,
            target_brand_id,
            gap_version,
            status,
            total_prompts,
            gap_count,
            refreshed_at,
            created_at,
            updated_at
        )
        SELECT
            experiment_id,
            project_id,
            target_brand_id,
            'site-rag-gap-v1',
            'completed',
            NULL,
            COUNT(*),
            MAX(updated_at),
            MIN(created_at),
            MAX(updated_at)
        FROM site_rag_gaps
        GROUP BY experiment_id, project_id, target_brand_id
        """
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_site_rag_gap_analyses_target_brand_id"),
        table_name="site_rag_gap_analyses",
    )
    op.drop_index(
        op.f("ix_site_rag_gap_analyses_status"),
        table_name="site_rag_gap_analyses",
    )
    op.drop_index(
        op.f("ix_site_rag_gap_analyses_refreshed_at"),
        table_name="site_rag_gap_analyses",
    )
    op.drop_index(
        op.f("ix_site_rag_gap_analyses_project_id"),
        table_name="site_rag_gap_analyses",
    )
    op.drop_index(
        op.f("ix_site_rag_gap_analyses_experiment_id"),
        table_name="site_rag_gap_analyses",
    )
    op.drop_table("site_rag_gap_analyses")
