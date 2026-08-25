import re

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.prompt import Prompt

from app.repositories.project_repository import (
    ProjectRepository,
)


class PromptUpdateService:

    @staticmethod
    def normalize_text(
        value: str,
    ) -> str:
        return re.sub(
            r"\s+",
            " ",
            value.strip().lower(),
        )

    @classmethod
    def update(
        cls,
        db: Session,
        project_id: int,
        prompt_id: int,
        data,
    ) -> Prompt:

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

        prompt = db.get(
            Prompt,
            prompt_id,
        )

        if (
            prompt is None
            or prompt.project_id
            != project_id
        ):
            raise HTTPException(
                status_code=404,
                detail="Prompt not found.",
            )

        text = re.sub(
            r"\s+",
            " ",
            data.text.strip(),
        )

        normalized = (
            cls.normalize_text(
                text
            )
        )

        other_prompts = list(
            db.scalars(
                select(Prompt)
                .where(
                    Prompt.project_id
                    == project_id,

                    Prompt.id
                    != prompt_id,
                )
            ).all()
        )

        duplicate = any(
            cls.normalize_text(
                item.text
            )
            == normalized
            for item
            in other_prompts
        )

        if duplicate:
            raise HTTPException(
                status_code=409,
                detail=(
                    "Another prompt in this "
                    "project already uses this text."
                ),
            )

        try:
            prompt.text = text

            prompt.category = (
                data.category
            )

            prompt.intent = (
                data.intent.strip()
                if (
                    data.intent
                    and data.intent.strip()
                )
                else None
            )

            # Keep is_active unchanged.

            db.commit()
            db.refresh(prompt)

        except Exception:
            db.rollback()
            raise

        return prompt
