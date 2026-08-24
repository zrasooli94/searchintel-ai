from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.repositories.brand_alias_repository import (
    BrandAliasRepository,
)
from app.repositories.brand_repository import (
    BrandRepository,
)
from app.services.brand_service import BrandService


class BrandAliasService:

    @staticmethod
    def create(
        db: Session,
        brand_id: int,
        alias: str,
    ):
        brand = BrandRepository.get_by_id(
            db,
            brand_id,
        )

        if brand is None:
            raise HTTPException(
                status_code=404,
                detail="Brand not found.",
            )

        alias = alias.strip()

        if len(alias) < 2:
            raise HTTPException(
                status_code=400,
                detail="Alias is too short.",
            )

        normalized = (
            BrandService.normalize_name(
                alias
            )
        )

        if normalized == brand.normalized_name:
            raise HTTPException(
                status_code=409,
                detail=(
                    "Alias is identical to "
                    "the canonical brand name."
                ),
            )

        existing_alias = (
            BrandAliasRepository
            .get_by_normalized_alias(
                db,
                normalized,
            )
        )

        if existing_alias:
            raise HTTPException(
                status_code=409,
                detail="Alias already exists.",
            )

        existing_brand = (
            BrandRepository
            .get_by_normalized_name(
                db,
                normalized,
            )
        )

        if (
            existing_brand
            and existing_brand.id != brand.id
        ):
            raise HTTPException(
                status_code=409,
                detail=(
                    "Alias conflicts with "
                    "another canonical brand."
                ),
            )

        record = BrandAliasRepository.create(
            db=db,
            brand_id=brand.id,
            alias=alias,
            normalized_alias=normalized,
        )

        db.commit()
        db.refresh(record)

        return record

    @staticmethod
    def list(
        db: Session,
        brand_id: int,
    ):
        brand = BrandRepository.get_by_id(
            db,
            brand_id,
        )

        if brand is None:
            raise HTTPException(
                status_code=404,
                detail="Brand not found.",
            )

        return BrandAliasRepository.list_by_brand(
            db,
            brand_id,
        )
