from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.prompt import Prompt


class PromptRepository:

    @staticmethod
    def create(
        db: Session,
        project_id: int,
        text: str,
        category: str,
        intent: str | None,
    ) -> Prompt:
        prompt = Prompt(
            project_id=project_id,
            text=text,
            category=category,
            intent=intent,
        )

        db.add(prompt)
        db.commit()
        db.refresh(prompt)

        return prompt

    @staticmethod
    def get_by_id(
        db: Session,
        prompt_id: int,
    ) -> Prompt | None:
        return db.get(
            Prompt,
            prompt_id,
        )

    @staticmethod
    def find_duplicate(
        db: Session,
        project_id: int,
        text: str,
    ) -> Prompt | None:
        statement = select(Prompt).where(
            Prompt.project_id == project_id,
            Prompt.text == text,
        )

        return db.scalar(statement)

    @staticmethod
    def list_by_project(
        db: Session,
        project_id: int,
    ) -> list[Prompt]:
        statement = (
            select(Prompt)
            .where(
                Prompt.project_id == project_id
            )
            .order_by(Prompt.id)
        )

        return list(
            db.scalars(statement).all()
        )
