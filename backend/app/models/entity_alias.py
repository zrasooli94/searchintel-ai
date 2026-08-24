from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.db.base import Base


class EntityAlias(Base):
    __tablename__ = "entity_aliases"

    __table_args__ = (
        UniqueConstraint(
            "entity_id",
            "normalized_alias",
            name="uq_entity_alias",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    entity_id: Mapped[int] = mapped_column(
        ForeignKey(
            "search_entities.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    alias: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    normalized_alias: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    entity = relationship(
        "SearchEntity",
        back_populates="aliases",
    )
