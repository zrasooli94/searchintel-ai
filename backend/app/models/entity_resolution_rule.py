from datetime import datetime

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class EntityResolutionRule(Base):
    __tablename__ = "entity_resolution_rules"

    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "normalized_name",
            name="uq_project_entity_resolution",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    project_id: Mapped[int] = mapped_column(
        ForeignKey(
            "projects.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    normalized_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    display_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True,
    )

    brand_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "brands.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    confidence: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=1.0,
    )

    source: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="system",
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
