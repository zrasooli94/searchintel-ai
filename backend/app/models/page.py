from datetime import datetime

from sqlalchemy import (
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


class Page(Base):
    __tablename__ = "pages"

    __table_args__ = (
        UniqueConstraint(
            "website_id",
            "url",
            name="uq_website_page_url",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    website_id: Mapped[int] = mapped_column(
        ForeignKey("websites.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    url: Mapped[str] = mapped_column(
        String(2048),
        nullable=False,
    )

    canonical_url: Mapped[str | None] = mapped_column(
        String(2048),
        nullable=True,
    )

    status_code: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    title: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    meta_description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    h1: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    h1_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    robots_meta: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    word_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    internal_link_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    external_link_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    content_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    content_hash: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )

    last_crawled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
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

    website = relationship(
        "Website",
        back_populates="pages",
    )
