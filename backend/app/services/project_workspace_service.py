from sqlalchemy.orm import Session

from app.repositories.geo_experiment_repository import (
    GeoExperimentRepository,
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


class ProjectWorkspaceService:

    @classmethod
    def list_all(
        cls,
        db: Session,
    ) -> list[dict]:

        projects = (
            ProjectRepository.list_all(db)
        )

        result = []

        for project in projects:

            brand_roles = (
                ProjectBrandRepository
                .list_brand_roles(
                    db,
                    project.id,
                )
            )

            target_rows = [
                brand
                for brand, role
                in brand_roles
                if role == "target"
            ]

            competitor_count = sum(
                role == "competitor"
                for _brand, role
                in brand_roles
            )

            target = (
                target_rows[0]
                if target_rows
                else None
            )

            website = None

            if target is not None:
                websites = (
                    WebsiteRepository
                    .list_by_brand(
                        db,
                        target.id,
                    )
                )

                primary = [
                    item
                    for item in websites
                    if item.is_primary
                ]

                if primary:
                    website = primary[0]
                elif websites:
                    website = websites[0]

            experiments = (
                GeoExperimentRepository
                .list_by_project(
                    db,
                    project.id,
                )
            )

            completed = [
                experiment
                for experiment in experiments
                if experiment.status
                == "completed"
            ]

            completed.sort(
                key=lambda experiment:
                    experiment.id,
                reverse=True,
            )

            latest_completed = (
                completed[0]
                if completed
                else None
            )

            result.append(
                {
                    "id":
                        project.id,

                    "name":
                        project.name,

                    "description":
                        project.description,

                    "target_brand_id":
                        (
                            target.id
                            if target
                            else None
                        ),

                    "target_brand":
                        (
                            target.name
                            if target
                            else None
                        ),

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

                    "competitor_count":
                        competitor_count,

                    "experiment_count":
                        len(experiments),

                    "completed_experiment_count":
                        len(completed),

                    "latest_completed_experiment_id":
                        (
                            latest_completed.id
                            if latest_completed
                            else None
                        ),

                    "latest_completed_experiment_name":
                        (
                            latest_completed.name
                            if latest_completed
                            else None
                        ),
                }
            )

        return result
