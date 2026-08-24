from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.brand_alias import BrandAlias


class BrandAliasRepository:

    @staticmethod
    def create(
        db: Session,
        brand_id: int,
        alias: str,
        normalized_alias: str,
    ) -> BrandAlias:
        record = BrandAlias(
            brand_id=brand_id,
            alias=alias,
            normalized_alias=normalized_alias,
        )

        db.add(record)
        db.flush()

        return record

    @staticmethod
    def get_by_normalized_alias(
        db: Session,
        normalized_alias: str,
    ) -> BrandAlias | None:
        statement = select(
            BrandAlias
        ).where(
            BrandAlias.normalized_alias
            == normalized_alias
        )

        return db.scalar(statement)

    @staticmethod
    def list_by_brand(
        db: Session,
        brand_id: int,
    ) -> list[BrandAlias]:
        statement = (
            select(BrandAlias)
            .where(
                BrandAlias.brand_id
                == brand_id
            )
            .order_by(
                BrandAlias.id
            )
        )

        return list(
            db.scalars(statement).all()
        )
