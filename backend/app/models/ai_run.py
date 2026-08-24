from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AIRun(Base):
    __tablename__ = "ai_runs"

    id: Mapped[int] = mapped_column(primary_key=True)

    experiment_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "geo_experiments.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    prompt_id: Mapped[int] = mapped_column(
        ForeignKey("prompts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    model_id: Mapped[int] = mapped_column(
        ForeignKey("ai_models.id"),
        nullable=False,
        index=True,
    )

    run_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="ad_hoc",
        server_default="ad_hoc",
        index=True,
    )

    include_in_metrics: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
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

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    latency_ms: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    input_tokens: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    output_tokens: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    estimated_cost: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 6),
        nullable=True,
    )

    error_message: Mapped[str | None] = mapped_column(
        String(2000),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    prompt = relationship(
        "Prompt",
        back_populates="runs",
    )

    model = relationship(
        "AIModel",
        back_populates="runs",
    )

    response = relationship(
        "AIResponse",
        back_populates="run",
        uselist=False,
        cascade="all, delete-orphan",
    )
