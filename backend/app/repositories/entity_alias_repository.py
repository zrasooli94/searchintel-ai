from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entity_alias import EntityAlias


class EntityAliasRepository:

    @staticmethod
    def get(
        db: Session,
        entity_id: int,
        normalized_alias: str,
    ) -> EntityAlias | None:

        statement = select(
            EntityAlias
        ).where(
            EntityAlias.entity_id
            == entity_id,
            EntityAlias.normalized_alias
            == normalized_alias,
        )

        return db.scalar(statement)

    @classmethod
    def create_if_missing(
        cls,
        db: Session,
        entity_id: int,
        alias: str,
        normalized_alias: str,
    ) -> EntityAlias:

        existing = cls.get(
            db,
            entity_id,
            normalized_alias,
        )

        if existing is not None:
            return existing

        record = EntityAlias(
            entity_id=entity_id,
            alias=alias,
            normalized_alias=normalized_alias,
        )

        db.add(record)
        db.flush()

        return record
