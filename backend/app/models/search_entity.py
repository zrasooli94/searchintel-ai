from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.db.base import Base


class SearchEntity(Base):
    __tablename__ = "search_entities"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    normalized_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    entity_type: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        index=True,
    )

    # Canonical Brand used for brand-level
    # metrics. Products/projects may roll up
    # to their owning commercial brand.
    rollup_brand_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "brands.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
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

    rollup_brand = relationship(
        "Brand"
    )

    aliases = relationship(
        "EntityAlias",
        back_populates="entity",
        cascade="all, delete-orphan",
    )

    outgoing_relationships = relationship(
        "EntityRelationship",
        foreign_keys=(
            "EntityRelationship.subject_entity_id"
        ),
        back_populates="subject",
        cascade="all, delete-orphan",
    )

    incoming_relationships = relationship(
        "EntityRelationship",
        foreign_keys=(
            "EntityRelationship.object_entity_id"
        ),
        back_populates="object",
        cascade="all, delete-orphan",
    )
