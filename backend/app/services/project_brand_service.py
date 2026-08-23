from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.project_brand import ProjectBrand
from app.repositories.brand_repository import BrandRepository
from app.repositories.project_brand_repository import (
    ProjectBrandRepository,
)
from app.repositories.project_repository import ProjectRepository
from app.schemas.project_brand import ProjectBrandCreate


class ProjectBrandService:

    @staticmethod
    def add_brand(
        db: Session,
        project_id: int,
        data: ProjectBrandCreate,
    ) -> ProjectBrand:
        project = ProjectRepository.get_by_id(
            db,
            project_id,
        )

        if project is None:
            raise HTTPException(
                status_code=404,
                detail="Project not found.",
            )

        brand = BrandRepository.get_by_id(
            db,
            data.brand_id,
        )

        if brand is None:
            raise HTTPException(
                status_code=404,
                detail="Brand not found.",
            )

        existing = ProjectBrandRepository.get_link(
            db,
            project_id,
            data.brand_id,
        )

        if existing:
            raise HTTPException(
                status_code=409,
                detail="Brand is already attached to this project.",
            )

        return ProjectBrandRepository.create(
            db=db,
            project_id=project_id,
            brand_id=data.brand_id,
            role=data.role,
        )

    @staticmethod
    def list_brands(
        db: Session,
        project_id: int,
    ) -> list[ProjectBrand]:
        project = ProjectRepository.get_by_id(
            db,
            project_id,
        )

        if project is None:
            raise HTTPException(
                status_code=404,
                detail="Project not found.",
            )

        return ProjectBrandRepository.list_by_project(
            db,
            project_id,
        )