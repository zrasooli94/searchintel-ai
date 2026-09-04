"""Distinguish the reviewed V1 import from naturally observed changes."""
from alembic import op
import sqlalchemy as sa

revision = "e91c4a7b302d"
down_revision = "d8a1f6b9c302"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("inbox_events", sa.Column("origin", sa.String(30), nullable=False,
                                          server_default="workflow"))
    # Reviewed V1 backfill was one PostgreSQL transaction (34 rows). Match that
    # exact import, not IDs, brands, or every event existing at deployment time.
    # Later natural events and all user lifecycle choices remain untouched.
    op.execute(sa.text("""
        UPDATE inbox_events SET origin = 'backfill'
        WHERE created_at = '2026-09-04T04:35:51.013004+00:00'
          AND event_type IN ('priority_new_high', 'priority_rechecked_unchanged')
    """))


def downgrade():
    op.drop_column("inbox_events", "origin")
