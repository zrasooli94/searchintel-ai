from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class BrandMention(Base):
    __tablename__ = "brand_mentions"

    id: Mapped[int] = mapped_column(primary_key=True)

    response_id: Mapped[int] = mapped_column(
        ForeignKey("ai_responses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    brand_id: Mapped[int | None] = mapped_column(
        ForeignKey("brands.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    entity_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "search_entities.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    mention_text: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    normalized_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    position: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    mention_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )

    is_target: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    resolution_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="unresolved",
    )

    confidence: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=1.0,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    response = relationship(
        "AIResponse",
        back_populates="brand_mentions",
    )

    brand = relationship("Brand")
