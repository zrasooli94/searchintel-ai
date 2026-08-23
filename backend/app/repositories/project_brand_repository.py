from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.project_brand import ProjectBrand


class ProjectBrandRepository:

    @staticmethod
    def create(
        db: Session,
        project_id: int,
        brand_id: int,
        role: str,
    ) -> ProjectBrand:
        project_brand = ProjectBrand(
            project_id=project_id,
            brand_id=brand_id,
            role=role,
        )

        db.add(project_brand)
        db.commit()
        db.refresh(project_brand)

        return project_brand

    @staticmethod
    def get_link(
        db: Session,
        project_id: int,
        brand_id: int,
    ) -> ProjectBrand | None:
        statement = select(ProjectBrand).where(
            ProjectBrand.project_id == project_id,
            ProjectBrand.brand_id == brand_id,
        )

        return db.scalar(statement)

    @staticmethod
    def list_by_project(
        db: Session,
        project_id: int,
    ) -> list[ProjectBrand]:
        statement = (
            select(ProjectBrand)
            .where(ProjectBrand.project_id == project_id)
            .order_by(ProjectBrand.id)
        )

        return list(
            db.scalars(statement).all()
        )