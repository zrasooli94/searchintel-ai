from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.project import Project


class ProjectRepository:

    @staticmethod
    def create(
        db: Session,
        name: str,
        description: str | None = None,
    ) -> Project:
        project = Project(
            name=name,
            description=description,
        )

        db.add(project)
        db.commit()
        db.refresh(project)

        return project

    @staticmethod
    def get_by_id(
        db: Session,
        project_id: int,
    ) -> Project | None:
        return db.get(Project, project_id)

    @staticmethod
    def list_all(
        db: Session,
    ) -> list[Project]:
        statement = select(Project).order_by(Project.id)

        return list(
            db.scalars(statement).all()
        )