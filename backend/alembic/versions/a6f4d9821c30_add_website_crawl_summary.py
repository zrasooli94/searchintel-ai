"""add website crawl summary

Revision ID: a6f4d9821c30
Revises: c31d8f2a4b70
Create Date: 2026-08-28 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a6f4d9821c30"
down_revision: Union[str, Sequence[str], None] = "c31d8f2a4b70"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "websites",
        sa.Column(
            "last_crawl_summary",
            sa.JSON(),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column(
        "websites",
        "last_crawl_summary",
    )
