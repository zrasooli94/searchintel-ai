from datetime import datetime

from sqlalchemy import (
    DateTime,
    Float,
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


class EntityRelationship(Base):
    __tablename__ = "entity_relationships"

    __table_args__ = (
        UniqueConstraint(
            "subject_entity_id",
            "object_entity_id",
            "relationship_type",
            name="uq_entity_relationship",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    subject_entity_id: Mapped[int] = mapped_column(
        ForeignKey(
            "search_entities.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    object_entity_id: Mapped[int] = mapped_column(
        ForeignKey(
            "search_entities.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    relationship_type: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
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

    subject = relationship(
        "SearchEntity",
        foreign_keys=[subject_entity_id],
        back_populates="outgoing_relationships",
    )

    object = relationship(
        "SearchEntity",
        foreign_keys=[object_entity_id],
        back_populates="incoming_relationships",
    )
