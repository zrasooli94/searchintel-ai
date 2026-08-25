from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.repositories.project_brand_repository import (
    ProjectBrandRepository,
)
from app.repositories.project_repository import (
    ProjectRepository,
)
from app.repositories.website_repository import (
    WebsiteRepository,
)


class ProjectCompetitorSummaryService:

    @classmethod
    def list(
        cls,
        db: Session,
        project_id: int,
    ) -> list[dict]:

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

        rows = (
            ProjectBrandRepository
            .list_brand_roles(
                db,
                project_id,
            )
        )

        result = []

        for brand, role in rows:
            if role != "competitor":
                continue

            websites = (
                WebsiteRepository
                .list_by_brand(
                    db,
                    brand.id,
                )
            )

            primary = next(
                (
                    item
                    for item in websites
                    if item.is_primary
                ),
                None,
            )

            website = (
                primary
                or (
                    websites[0]
                    if websites
                    else None
                )
            )

            result.append(
                {
                    "brand_id":
                        brand.id,

                    "name":
                        brand.name,

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
                }
            )

        result.sort(
            key=lambda item:
                item["name"].lower()
        )

        return result
