import re

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.brand import Brand
from app.repositories.brand_repository import BrandRepository
from app.schemas.brand import BrandCreate


class BrandService:

    @staticmethod
    def normalize_name(name: str) -> str:
        normalized = name.strip().lower()
        normalized = re.sub(r"\s+", " ", normalized)

        return normalized

    @classmethod
    def create(
        cls,
        db: Session,
        data: BrandCreate,
    ) -> Brand:
        name = data.name.strip()

        if not name:
            raise HTTPException(
                status_code=400,
                detail="Brand name cannot be empty.",
            )

        normalized_name = cls.normalize_name(name)

        existing = BrandRepository.get_by_normalized_name(
            db,
            normalized_name,
        )

        if existing:
            raise HTTPException(
                status_code=409,
                detail="Brand already exists.",
            )

        return BrandRepository.create(
            db=db,
            name=name,
            normalized_name=normalized_name,
            description=data.description,
        )

    @staticmethod
    def get(
        db: Session,
        brand_id: int,
    ) -> Brand:
        brand = BrandRepository.get_by_id(
            db,
            brand_id,
        )

        if brand is None:
            raise HTTPException(
                status_code=404,
                detail="Brand not found.",
            )

        return brand

    @staticmethod
    def list_all(
        db: Session,
    ) -> list[Brand]:
        return BrandRepository.list_all(db)
