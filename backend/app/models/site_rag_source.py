from datetime import datetime

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.db.base import Base


class SiteRAGSource(Base):
    __tablename__ = "site_rag_sources"

    __table_args__ = (
        UniqueConstraint(
            "response_id",
            "rank",
            name="uq_site_rag_source_rank",
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

    page_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "pages.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    rank: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    chunk_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    relevance_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    url: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    title: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    excerpt: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    response = relationship(
        "AIResponse",
        back_populates="site_rag_sources",
    )

    page = relationship(
        "Page",
    )
