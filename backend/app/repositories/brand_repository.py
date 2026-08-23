from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.brand import Brand


class BrandRepository:

    @staticmethod
    def create(
        db: Session,
        name: str,
        normalized_name: str,
        description: str | None = None,
    ) -> Brand:
        brand = Brand(
            name=name,
            normalized_name=normalized_name,
            description=description,
        )

        db.add(brand)
        db.commit()
        db.refresh(brand)

        return brand

    @staticmethod
    def get_by_id(
        db: Session,
        brand_id: int,
    ) -> Brand | None:
        return db.get(Brand, brand_id)

    @staticmethod
    def get_by_normalized_name(
        db: Session,
        normalized_name: str,
    ) -> Brand | None:
        statement = select(Brand).where(
            Brand.normalized_name == normalized_name
        )

        return db.scalar(statement)

    @staticmethod
    def list_all(
        db: Session,
    ) -> list[Brand]:
        statement = select(Brand).order_by(Brand.id)

        return list(
            db.scalars(statement).all()
        )