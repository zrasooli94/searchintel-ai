from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.project_priority import ProjectPriority


class ProjectPriorityRepository:
    @staticmethod
    def list_by_project(db: Session, project_id: int, include_resolved: bool = True) -> list[ProjectPriority]:
        statement = select(ProjectPriority).where(ProjectPriority.project_id == project_id)
        if not include_resolved:
            statement = statement.where(ProjectPriority.is_resolved.is_(False))
        return list(db.scalars(statement.order_by(ProjectPriority.priority_score.desc(), ProjectPriority.id)).all())

    @staticmethod
    def get(db: Session, project_id: int, priority_id: int) -> ProjectPriority | None:
        return db.scalar(select(ProjectPriority).where(
            ProjectPriority.id == priority_id,
            ProjectPriority.project_id == project_id,
        ))

    @staticmethod
    def by_key(db: Session, project_id: int) -> dict[str, ProjectPriority]:
        return {item.stable_key: item for item in ProjectPriorityRepository.list_by_project(db, project_id)}

