from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entity_resolution_rule import (
    EntityResolutionRule,
)


class EntityResolutionRuleRepository:

    @staticmethod
    def get_by_id(
        db: Session,
        rule_id: int,
    ) -> EntityResolutionRule | None:
        return db.get(
            EntityResolutionRule,
            rule_id,
        )

    @staticmethod
    def get(
        db: Session,
        project_id: int,
        normalized_name: str,
    ) -> EntityResolutionRule | None:

        statement = select(
            EntityResolutionRule
        ).where(
            EntityResolutionRule.project_id
            == project_id,
            EntityResolutionRule.normalized_name
            == normalized_name,
        )

        return db.scalar(statement)

    @classmethod
    def upsert(
        cls,
        db: Session,
        project_id: int,
        normalized_name: str,
        display_name: str | None,
        status: str,
        brand_id: int | None = None,
        entity_id: int | None = None,
        entity_type: str | None = None,
        confidence: float = 1.0,
        source: str = "system",
    ) -> EntityResolutionRule:

        rule = cls.get(
            db,
            project_id,
            normalized_name,
        )

        if rule is None:
            rule = EntityResolutionRule(
                project_id=project_id,
                normalized_name=normalized_name,
                display_name=display_name,
                status=status,
                brand_id=brand_id,
                entity_id=entity_id,
                entity_type=entity_type,
                confidence=confidence,
                source=source,
            )

            db.add(rule)

        else:
            rule.display_name = display_name
            rule.status = status
            rule.brand_id = brand_id
            rule.entity_id = entity_id
            rule.entity_type = entity_type
            rule.confidence = confidence
            rule.source = source

        db.flush()

        return rule

    @staticmethod
    def list_by_status(
        db: Session,
        project_id: int,
        status: str,
    ) -> list[EntityResolutionRule]:

        statement = (
            select(EntityResolutionRule)
            .where(
                EntityResolutionRule.project_id
                == project_id,
                EntityResolutionRule.status
                == status,
            )
            .order_by(
                EntityResolutionRule.id
            )
        )

        return list(
            db.scalars(statement).all()
        )

    @staticmethod
    def set_classification(
        db: Session,
        rule: EntityResolutionRule,
        entity_type: str,
        proposed_parent_name: str | None,
        proposed_relationship_type: str | None,
        classification_confidence: float,
        classification_source: str,
    ) -> EntityResolutionRule:

        rule.entity_type = entity_type
        rule.proposed_parent_name = (
            proposed_parent_name
        )
        rule.proposed_relationship_type = (
            proposed_relationship_type
        )
        rule.classification_confidence = (
            classification_confidence
        )
        rule.classification_source = (
            classification_source
        )

        db.flush()

        return rule
