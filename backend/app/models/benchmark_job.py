from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class BenchmarkJob(Base):
    __tablename__ = "benchmark_jobs"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    experiment_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "geo_experiments.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    project_id: Mapped[int] = mapped_column(
        ForeignKey(
            "projects.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    model_id: Mapped[int] = mapped_column(
        ForeignKey(
            "ai_models.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    benchmark_mode: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="memory",
        server_default="memory",
        index=True,
    )

    config_snapshot: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        server_default="{}",
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="pending",
        index=True,
    )

    total_prompts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    completed_runs: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    failed_runs: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
