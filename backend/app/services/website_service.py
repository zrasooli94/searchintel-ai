from urllib.parse import urlparse

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.website import Website
from app.repositories.brand_repository import BrandRepository
from app.repositories.website_repository import WebsiteRepository
from app.schemas.website import WebsiteCreate


class WebsiteService:

    @staticmethod
    def normalize_domain(url: str) -> str:
        hostname = urlparse(url).hostname

        if hostname is None:
            raise HTTPException(
                status_code=400,
                detail="Invalid website URL.",
            )

        hostname = hostname.lower()

        if hostname.startswith("www."):
            hostname = hostname[4:]

        return hostname

    @classmethod
    def create(
        cls,
        db: Session,
        brand_id: int,
        data: WebsiteCreate,
    ) -> Website:
        brand = BrandRepository.get_by_id(
            db,
            brand_id,
        )

        if brand is None:
            raise HTTPException(
                status_code=404,
                detail="Brand not found.",
            )

        base_url = str(data.base_url)
        domain = cls.normalize_domain(base_url)

        existing = WebsiteRepository.get_by_brand_domain(
            db,
            brand_id,
            domain,
        )

        if existing:
            raise HTTPException(
                status_code=409,
                detail="Website already exists for this brand.",
            )

        return WebsiteRepository.create(
            db=db,
            brand_id=brand_id,
            domain=domain,
            base_url=base_url,
            is_primary=data.is_primary,
        )

    @staticmethod
    def get(
        db: Session,
        website_id: int,
    ) -> Website:
        website = WebsiteRepository.get_by_id(
            db,
            website_id,
        )

        if website is None:
            raise HTTPException(
                status_code=404,
                detail="Website not found.",
            )

        return website