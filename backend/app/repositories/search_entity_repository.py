from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.search_entity import SearchEntity


class SearchEntityRepository:

    @staticmethod
    def get_by_id(
        db: Session,
        entity_id: int,
    ) -> SearchEntity | None:
        return db.get(
            SearchEntity,
            entity_id,
        )

    @staticmethod
    def get_brand_entity_by_brand_id(
        db: Session,
        brand_id: int,
    ) -> SearchEntity | None:

        statement = (
            select(SearchEntity)
            .where(
                SearchEntity.rollup_brand_id
                == brand_id,
                SearchEntity.entity_type
                == "brand",
            )
            .order_by(
                SearchEntity.id
            )
            .limit(1)
        )

        return db.scalar(statement)

    @staticmethod
    def create(
        db: Session,
        name: str,
        normalized_name: str,
        entity_type: str,
        rollup_brand_id: int | None = None,
        description: str | None = None,
    ) -> SearchEntity:

        entity = SearchEntity(
            name=name,
            normalized_name=normalized_name,
            entity_type=entity_type,
            rollup_brand_id=rollup_brand_id,
            description=description,
        )

        db.add(entity)
        db.flush()

        return entity
