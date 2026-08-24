from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entity_relationship import (
    EntityRelationship,
)


class EntityRelationshipRepository:

    @staticmethod
    def get(
        db: Session,
        subject_entity_id: int,
        object_entity_id: int,
        relationship_type: str,
    ) -> EntityRelationship | None:

        statement = select(
            EntityRelationship
        ).where(
            EntityRelationship.subject_entity_id
            == subject_entity_id,
            EntityRelationship.object_entity_id
            == object_entity_id,
            EntityRelationship.relationship_type
            == relationship_type,
        )

        return db.scalar(statement)

    @classmethod
    def create_if_missing(
        cls,
        db: Session,
        subject_entity_id: int,
        object_entity_id: int,
        relationship_type: str,
        confidence: float = 1.0,
        source: str = "manual_resolution",
    ) -> EntityRelationship:

        existing = cls.get(
            db,
            subject_entity_id,
            object_entity_id,
            relationship_type,
        )

        if existing is not None:
            return existing

        relationship = EntityRelationship(
            subject_entity_id=subject_entity_id,
            object_entity_id=object_entity_id,
            relationship_type=relationship_type,
            confidence=confidence,
            source=source,
        )

        db.add(relationship)
        db.flush()

        return relationship
