from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Citation(Base):
    __tablename__ = "citations"

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

    url: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    domain: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )

    title: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    position: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    response = relationship(
        "AIResponse",
        back_populates="citations",
    )

    brand = relationship("Brand")
