from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    JSON,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class GeoActionPlan(Base):
    __tablename__ = "geo_action_plans"

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

    target_brand_id: Mapped[int] = mapped_column(
        ForeignKey(
            "brands.id",
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
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="completed",
    )

    strategy_summary: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    baseline_metrics: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
    )

    source_diagnosis_ids: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
    )

    recommended_sequence: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    risks_and_limits: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
