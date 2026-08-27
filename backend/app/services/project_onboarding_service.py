from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.brand import Brand
from app.models.project import Project
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


class ProjectOnboardingService:

    @classmethod
    def onboard(
        cls,
        db: Session,
        data,
    ) -> dict:

        project_name = (
            data.project_name.strip()
        )

        target_brand_name = (
            data.target_brand.strip()
        )

        website_url = str(
            data.website_url
        )

        domain = (
            WebsiteService.normalize_domain(
                website_url
            )
        )

        if len(project_name) < 3:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Project name must contain "
                    "at least 3 characters."
                ),
            )

        if not target_brand_name:
            raise HTTPException(
                status_code=400,
                detail="Brand name cannot be empty.",
            )

        existing_project = (
            ProjectRepository.get_by_name(
                db,
                project_name,
            )
        )

        if existing_project is not None:
            raise HTTPException(
                status_code=409,
                detail=(
                    "A project with this name "
                    "already exists."
                ),
            )

        normalized_brand = (
            BrandService.normalize_name(
                target_brand_name
            )
        )

        brand_created = False
        website_created = False
        canonical_entity_created = False

        try:
            # ---------------------------------
            # Reuse or create global Brand
            # ---------------------------------

            brand = (
                BrandRepository
                .get_by_normalized_name(
                    db,
                    normalized_brand,
                )
            )

            if brand is None:
                brand = Brand(
                    name=target_brand_name,
                    normalized_name=
                        normalized_brand,
                )

                db.add(brand)
                db.flush()

                brand_created = True

            # ---------------------------------
            # Existing primary-domain safety
            # ---------------------------------

            existing_websites = (
                WebsiteRepository
                .list_by_brand(
                    db,
                    brand.id,
                )
            )

            primary_websites = [
                website
                for website
                in existing_websites
                if website.is_primary
            ]

            if primary_websites:
                primary = primary_websites[0]

                if primary.domain != domain:
                    raise HTTPException(
                        status_code=409,
                        detail=(
                            "This brand already has "
                            "a different primary "
                            "website: "
                            f"{primary.domain}"
                        ),
                    )

            # ---------------------------------
            # Create Project
            # ---------------------------------

            project = Project(
                name=project_name,
                description=(
                    data.project_description
                ),
            )

            db.add(project)
            db.flush()

            # ---------------------------------
            # Attach target Brand
            # ---------------------------------

            project_brand = ProjectBrand(
                project_id=project.id,
                brand_id=brand.id,
                role="target",
            )

            db.add(project_brand)
            db.flush()

            # ---------------------------------
            # Reuse or create Website
            # ---------------------------------

            website = (
                WebsiteRepository
                .get_by_brand_domain(
                    db,
                    brand.id,
                    domain,
                )
            )

            if website is None:
                website = Website(
                    brand_id=brand.id,
                    domain=domain,
                    base_url=website_url,
                    is_primary=True,
                )

                db.add(website)
                db.flush()

                website_created = True

            elif not primary_websites:
                website.is_primary = True
                db.flush()

            # ---------------------------------
            # Canonical target SearchEntity
            # ---------------------------------

            entity = db.scalar(
                select(SearchEntity)
                .where(
                    SearchEntity.rollup_brand_id
                    == brand.id,

                    SearchEntity.entity_type
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
                    rollup_brand_id=brand.id,
                    description=(
                        "Canonical target brand "
                        "entity."
                    ),
                )

                db.add(entity)
                db.flush()

                canonical_entity_created = True

            db.commit()

            db.refresh(project)
            db.refresh(brand)
            db.refresh(website)

        except Exception:
            db.rollback()
            raise

        return {
            "project_id":
                project.id,

            "project_name":
                project.name,

            "target_brand_id":
                brand.id,

            "target_brand":
                brand.name,

            "website_id":
                website.id,

            "domain":
                website.domain,

            "base_url":
                website.base_url,

            "brand_created":
                brand_created,

            "website_created":
                website_created,

            "canonical_entity_created":
                canonical_entity_created,

            "setup_status":
                "workspace_created",
        }
