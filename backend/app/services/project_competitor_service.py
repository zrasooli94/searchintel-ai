from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.brand import Brand
from app.models.project_brand import (
    ProjectBrand,
)
from app.models.search_entity import (
    SearchEntity,
)
from app.models.website import Website

from app.repositories.brand_repository import (
    BrandRepository,
)
from app.repositories.project_brand_repository import (
    ProjectBrandRepository,
)
from app.repositories.project_repository import (
    ProjectRepository,
)
from app.repositories.website_repository import (
    WebsiteRepository,
)

from app.services.brand_service import (
    BrandService,
)
from app.services.website_service import (
    WebsiteService,
)


class ProjectCompetitorService:

    @classmethod
    def add(
        cls,
        db: Session,
        project_id: int,
        data,
        commit: bool = True,
    ) -> dict:

        project = (
            ProjectRepository.get_by_id(
                db,
                project_id,
            )
        )

        if project is None:
            raise HTTPException(
                status_code=404,
                detail="Project not found.",
            )

        name = data.name.strip()

        normalized_name = (
            BrandService.normalize_name(
                name
            )
        )

        brand_created = False
        website_created = False
        canonical_entity_created = False

        website_url = (
            str(data.website_url)
            if data.website_url
            else None
        )

        domain = (
            WebsiteService.normalize_domain(
                website_url
            )
            if website_url
            else None
        )

        try:
            # ---------------------------------
            # Reuse / create Brand
            # ---------------------------------

            brand = (
                BrandRepository
                .get_by_normalized_name(
                    db,
                    normalized_name,
                )
            )

            if brand is None:
                brand = Brand(
                    name=name,
                    normalized_name=
                        normalized_name,
                )

                db.add(brand)
                db.flush()

                brand_created = True

            # ---------------------------------
            # Project relationship
            # ---------------------------------

            existing_link = (
                ProjectBrandRepository
                .get_link(
                    db,
                    project_id,
                    brand.id,
                )
            )

            if existing_link:
                if (
                    existing_link.role
                    == "competitor"
                ):
                    raise HTTPException(
                        status_code=409,
                        detail=(
                            "Competitor is already "
                            "configured for this project."
                        ),
                    )

                raise HTTPException(
                    status_code=409,
                    detail=(
                        "This brand is already "
                        "attached to the project as "
                        f"{existing_link.role}."
                    ),
                )

            project_brand = ProjectBrand(
                project_id=project_id,
                brand_id=brand.id,
                role="competitor",
            )

            db.add(project_brand)
            db.flush()

            # ---------------------------------
            # Website
            # ---------------------------------

            website = None

            if domain and website_url:
                website = (
                    WebsiteRepository
                    .get_by_brand_domain(
                        db,
                        brand.id,
                        domain,
                    )
                )

                if website is None:
                    existing_websites = (
                        WebsiteRepository
                        .list_by_brand(
                            db,
                            brand.id,
                        )
                    )

                    has_primary = any(
                        item.is_primary
                        for item
                        in existing_websites
                    )

                    website = Website(
                        brand_id=brand.id,
                        domain=domain,
                        base_url=website_url,
                        is_primary=(
                            not has_primary
                        ),
                    )

                    db.add(website)
                    db.flush()

                    website_created = True

            # ---------------------------------
            # Canonical entity
            # ---------------------------------

            entity = db.scalar(
                select(SearchEntity)
                .where(
                    SearchEntity
                    .rollup_brand_id
                    == brand.id,

                    SearchEntity
                    .entity_type
                    == "brand",
                )
                .order_by(
                    SearchEntity.id
                )
                .limit(1)
            )

            if entity is None:
                entity = SearchEntity(
                    name=brand.name,
                    normalized_name=
                        brand.normalized_name,
                    entity_type="brand",
                    rollup_brand_id=
                        brand.id,
                    description=(
                        "Canonical competitor "
                        "brand entity."
                    ),
                )

                db.add(entity)
                db.flush()

                canonical_entity_created = True

            if commit:
                db.commit()
                db.refresh(brand)
                if website:
                    db.refresh(website)
            else:
                db.flush()

        except Exception:
            db.rollback()
            raise

        return {
            "brand_id":
                brand.id,

            "name":
                brand.name,

            "role":
                "competitor",

            "website_id":
                (
                    website.id
                    if website
                    else None
                ),

            "domain":
                (
                    website.domain
                    if website
                    else None
                ),

            "base_url":
                (
                    website.base_url
                    if website
                    else None
                ),

            "brand_created":
                brand_created,

            "website_created":
                website_created,

            "canonical_entity_created":
                canonical_entity_created,
        }
