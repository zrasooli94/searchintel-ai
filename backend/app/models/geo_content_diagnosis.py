from datetime import datetime

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    JSON,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class GeoContentDiagnosis(Base):
    __tablename__ = "geo_content_diagnoses"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    opportunity_id: Mapped[int] = mapped_column(
        ForeignKey(
            "geo_prompt_opportunities.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
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
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="completed",
    )

    confidence: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )

    analysis: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
    )

    evidence_page_ids: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    evidence_run_ids: Mapped[list] = mapped_column(
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
