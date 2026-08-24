from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class WebSearchSource(Base):
    __tablename__ = "web_search_sources"

    __table_args__ = (
        UniqueConstraint(
            "response_id",
            "search_call_index",
            "source_position",
            name="uq_web_search_source_position",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    response_id: Mapped[int] = mapped_column(
        ForeignKey(
            "ai_responses.id",
            ondelete="CASCADE",
        ),
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

    entity_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "search_entities.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    search_call_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    source_position: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    search_query: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
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

    is_cited: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    response = relationship(
        "AIResponse",
        back_populates="web_search_sources",
    )

    brand = relationship("Brand")
