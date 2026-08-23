from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    JSON,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AIResponse(Base):
    __tablename__ = "ai_responses"

    id: Mapped[int] = mapped_column(primary_key=True)

    run_id: Mapped[int] = mapped_column(
        ForeignKey("ai_runs.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    response_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    raw_response: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    visibility_analyzed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    run = relationship(
        "AIRun",
        back_populates="response",
    )

    brand_mentions = relationship(
        "BrandMention",
        back_populates="response",
        cascade="all, delete-orphan",
    )

    citations = relationship(
        "Citation",
        back_populates="response",
        cascade="all, delete-orphan",
    )
