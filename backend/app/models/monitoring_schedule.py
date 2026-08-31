from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MonitoringSchedule(Base):
    __tablename__ = "monitoring_schedules"
    __table_args__ = (UniqueConstraint("project_id", "mode", name="uq_monitoring_project_mode"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    mode: Mapped[str] = mapped_column(String(30), index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    cadence_hours: Mapped[int] = mapped_column(Integer, default=168)
    next_due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    last_attempted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_successful_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_result: Mapped[dict] = mapped_column(JSON, default=dict, server_default="{}")
    source_benchmark_job_id: Mapped[int | None] = mapped_column(ForeignKey("benchmark_jobs.id", ondelete="SET NULL"))
    model_id: Mapped[int | None] = mapped_column(ForeignKey("ai_models.id", ondelete="SET NULL"))
    prompt_count: Mapped[int | None] = mapped_column(Integer)
    run_after_crawl: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    failure_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

