from datetime import datetime

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SiteRAGGap(Base):
    __tablename__ = "site_rag_gaps"

    __table_args__ = (
        UniqueConstraint(
            "experiment_id",
            "prompt_id",
            name="uq_site_rag_gap_experiment_prompt",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    experiment_id: Mapped[int] = mapped_column(
        ForeignKey(
            "geo_experiments.id",
            ondelete="CASCADE",
        ),
        nullable=False,
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

    prompt_id: Mapped[int] = mapped_column(
        ForeignKey(
            "prompts.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    target_brand_id: Mapped[int] = mapped_column(
        ForeignKey(
            "brands.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    prompt_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    intent: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    run_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    answerable_runs: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    unsupported_runs: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    answerability_rate: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    unsupported_rate: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    gap_type: Mapped[str] = mapped_column(
        String(60),
        nullable=False,
        index=True,
    )

    gap_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    priority: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )

    evidence: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    recommendation: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
