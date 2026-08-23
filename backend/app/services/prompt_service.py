from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.prompt import Prompt
from app.repositories.project_repository import ProjectRepository
from app.repositories.prompt_repository import PromptRepository
from app.schemas.prompt import PromptCreate


class PromptService:

    @staticmethod
    def create(
        db: Session,
        project_id: int,
        data: PromptCreate,
    ) -> Prompt:
        project = ProjectRepository.get_by_id(
            db,
            project_id,
        )

        if project is None:
            raise HTTPException(
                status_code=404,
                detail="Project not found.",
            )

        text = data.text.strip()

        if len(text) < 5:
            raise HTTPException(
                status_code=400,
                detail="Prompt is too short.",
            )

        existing = PromptRepository.find_duplicate(
            db,
            project_id,
            text,
        )

        if existing:
            raise HTTPException(
                status_code=409,
                detail="Prompt already exists in this project.",
            )

        return PromptRepository.create(
            db=db,
            project_id=project_id,
            text=text,
            category=data.category,
            intent=data.intent,
        )

    @staticmethod
    def list_by_project(
        db: Session,
        project_id: int,
    ) -> list[Prompt]:
        project = ProjectRepository.get_by_id(
            db,
            project_id,
        )

        if project is None:
            raise HTTPException(
                status_code=404,
                detail="Project not found.",
            )

        return PromptRepository.list_by_project(
            db,
            project_id,
        )
