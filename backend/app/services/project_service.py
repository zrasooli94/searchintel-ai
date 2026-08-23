from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.project import Project
from app.repositories.project_repository import ProjectRepository
from app.schemas.project import ProjectCreate


class ProjectService:

    @staticmethod
    def create(
        db: Session,
        data: ProjectCreate,
    ) -> Project:
        name = data.name.strip()

        if len(name) < 3:
            raise HTTPException(
                status_code=400,
                detail="Project name must contain at least 3 characters.",
            )

        return ProjectRepository.create(
            db=db,
            name=name,
            description=data.description,
        )

    @staticmethod
    def get(
        db: Session,
        project_id: int,
    ) -> Project:
        project = ProjectRepository.get_by_id(
            db,
            project_id,
        )

        if project is None:
            raise HTTPException(
                status_code=404,
                detail="Project not found.",
            )

        return project

    @staticmethod
    def list_all(
        db: Session,
    ) -> list[Project]:
        return ProjectRepository.list_all(db)