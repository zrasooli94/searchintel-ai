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


class GeoActionItem(Base):
    __tablename__ = "geo_action_items"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    action_plan_id: Mapped[int] = mapped_column(
        ForeignKey(
            "geo_action_plans.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    sort_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    priority: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )

    action_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    rationale: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    target_page: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    impacted_prompt_ids: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    impacted_opportunity_ids: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    implementation_steps: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    evidence: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    success_metrics: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    dependencies: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    effort: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="medium",
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="open",
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
