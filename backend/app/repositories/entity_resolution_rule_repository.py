from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entity_resolution_rule import (
    EntityResolutionRule,
)


class EntityResolutionRuleRepository:

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
                confidence=confidence,
                source=source,
            )

            db.add(rule)

        else:
            rule.display_name = display_name
            rule.status = status
            rule.brand_id = brand_id
            rule.confidence = confidence
            rule.source = source

        db.flush()

        return rule
