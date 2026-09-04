"""Persist agency inbox events and reconciliation checkpoints."""
from alembic import op
import sqlalchemy as sa

revision = "d8a1f6b9c302"
down_revision = "b7d5f0e3a842"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("inbox_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("event_type", sa.String(80), nullable=False),
        sa.Column("severity", sa.String(10), nullable=False),
        sa.Column("source_mode", sa.String(30), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("evidence", sa.JSON(), nullable=False),
        sa.Column("related_ids", sa.JSON(), nullable=False),
        sa.Column("evidence_path", sa.String(255), nullable=False),
        sa.Column("dedup_key", sa.String(64), nullable=False, unique=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("status", sa.String(10), nullable=False, server_default="unread"),
        sa.CheckConstraint("status IN ('unread', 'read', 'archived')", name="ck_inbox_status"),
        sa.CheckConstraint("severity IN ('high', 'medium', 'low')", name="ck_inbox_severity"))
    for field in ("project_id", "event_type", "severity", "source_mode", "status"):
        op.create_index(f"ix_inbox_events_{field}", "inbox_events", [field])
    op.create_table("inbox_checkpoints",
        sa.Column("key", sa.String(255), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False))
    op.create_index("ix_inbox_checkpoints_project_id", "inbox_checkpoints", ["project_id"])


def downgrade():
    op.drop_table("inbox_checkpoints")
    op.drop_table("inbox_events")
