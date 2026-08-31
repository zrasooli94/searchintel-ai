"""add durable monitoring schedules

Revision ID: b7d5f0e3a842
Revises: a6c4e9d2f731
"""
from alembic import op
import sqlalchemy as sa

revision = "b7d5f0e3a842"
down_revision = "a6c4e9d2f731"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("monitoring_schedules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("mode", sa.String(30), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("cadence_hours", sa.Integer(), nullable=False, server_default="168"),
        sa.Column("next_due_at", sa.DateTime(timezone=True)), sa.Column("last_attempted_at", sa.DateTime(timezone=True)),
        sa.Column("last_successful_at", sa.DateTime(timezone=True)), sa.Column("last_result", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("source_benchmark_job_id", sa.Integer(), sa.ForeignKey("benchmark_jobs.id", ondelete="SET NULL")),
        sa.Column("model_id", sa.Integer(), sa.ForeignKey("ai_models.id", ondelete="SET NULL")), sa.Column("prompt_count", sa.Integer()),
        sa.Column("run_after_crawl", sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column("failure_message", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("project_id", "mode", name="uq_monitoring_project_mode"))
    op.create_index("ix_monitoring_schedules_project_id", "monitoring_schedules", ["project_id"])
    op.create_index("ix_monitoring_schedules_mode", "monitoring_schedules", ["mode"])
    op.create_index("ix_monitoring_schedules_next_due_at", "monitoring_schedules", ["next_due_at"])
    op.create_table("monitoring_runs",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("schedule_id", sa.Integer(), sa.ForeignKey("monitoring_schedules.id", ondelete="CASCADE"), nullable=False),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False), sa.Column("mode", sa.String(30), nullable=False),
        sa.Column("status", sa.String(30), nullable=False), sa.Column("benchmark_job_id", sa.Integer(), sa.ForeignKey("benchmark_jobs.id", ondelete="SET NULL")),
        sa.Column("technical_audit_id", sa.Integer(), sa.ForeignKey("technical_audits.id", ondelete="SET NULL")), sa.Column("change_classification", sa.String(30)),
        sa.Column("change_evidence", sa.JSON(), nullable=False, server_default="{}"), sa.Column("error_message", sa.Text()),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()), sa.Column("completed_at", sa.DateTime(timezone=True)))
    for name, column in (("schedule_id", "schedule_id"), ("project_id", "project_id"), ("mode", "mode"), ("status", "status")):
        op.create_index(f"ix_monitoring_runs_{name}", "monitoring_runs", [column])


def downgrade():
    op.drop_table("monitoring_runs")
    op.drop_table("monitoring_schedules")
