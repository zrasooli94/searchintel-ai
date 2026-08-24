from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.website import Website
from app.models.project_brand import ProjectBrand


class WebsiteRepository:

    @staticmethod
    def create(
        db: Session,
        brand_id: int,
        domain: str,
        base_url: str,
        is_primary: bool,
    ) -> Website:
        website = Website(
            brand_id=brand_id,
            domain=domain,
            base_url=base_url,
            is_primary=is_primary,
        )

        db.add(website)
        db.commit()
        db.refresh(website)

        return website

    @staticmethod
    def get_by_id(
        db: Session,
        website_id: int,
    ) -> Website | None:
        return db.get(Website, website_id)

    @staticmethod
    def get_by_brand_domain(
        db: Session,
        brand_id: int,
        domain: str,
    ) -> Website | None:
        statement = select(Website).where(
            Website.brand_id == brand_id,
            Website.domain == domain,
        )

        return db.scalar(statement)

    @staticmethod
    def list_by_brand(
        db: Session,
        brand_id: int,
    ) -> list[Website]:
        statement = select(Website).where(
            Website.brand_id == brand_id
        )

        return list(
            db.scalars(statement).all()
        )


    @staticmethod
    def list_domain_brand_pairs_by_project(
        db: Session,
        project_id: int,
    ) -> list[tuple[str, int]]:

        statement = (
            select(
                Website.domain,
                Website.brand_id,
            )
            .join(
                ProjectBrand,
                ProjectBrand.brand_id
                == Website.brand_id,
            )
            .where(
                ProjectBrand.project_id
                == project_id
            )
        )

        return [
            (domain.lower(), brand_id)
            for domain, brand_id
            in db.execute(statement).all()
        ]
