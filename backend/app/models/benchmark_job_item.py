from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class BenchmarkJobItem(Base):
    __tablename__ = "benchmark_job_items"

    __table_args__ = (
        UniqueConstraint(
            "benchmark_job_id",
            "prompt_id",
            name="uq_benchmark_job_prompt",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    benchmark_job_id: Mapped[int] = mapped_column(
        ForeignKey(
            "benchmark_jobs.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    prompt_id: Mapped[int] = mapped_column(
        ForeignKey(
            "prompts.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    prompt_text_snapshot: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    ai_run_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "ai_runs.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        unique=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="pending",
        index=True,
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
