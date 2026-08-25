from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.prompt import Prompt

from app.repositories.project_repository import (
    ProjectRepository,
)


class PromptActiveSetService:

    @classmethod
    def update(
        cls,
        db: Session,
        project_id: int,
        prompt_ids: list[int],
    ) -> dict:

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

        prompts = list(
            db.scalars(
                select(Prompt)
                .where(
                    Prompt.project_id
                    == project_id
                )
                .order_by(
                    Prompt.id
                )
            ).all()
        )

        if not prompts:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Project has no prompts."
                ),
            )

        project_ids = {
            prompt.id
            for prompt in prompts
        }

        requested_ids = set(
            prompt_ids
        )

        unknown_ids = (
            requested_ids
            - project_ids
        )

        if unknown_ids:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Some prompt IDs do not "
                    "belong to this project: "
                    + ", ".join(
                        str(value)
                        for value
                        in sorted(
                            unknown_ids
                        )
                    )
                ),
            )

        try:
            for prompt in prompts:
                prompt.is_active = (
                    prompt.id
                    in requested_ids
                )

            db.commit()

        except Exception:
            db.rollback()
            raise

        active_ids = [
            prompt.id
            for prompt in prompts
            if prompt.is_active
        ]

        return {
            "project_id":
                project_id,

            "total_prompts":
                len(prompts),

            "active_prompts":
                len(active_ids),

            "inactive_prompts":
                len(prompts)
                - len(active_ids),

            "active_prompt_ids":
                active_ids,
        }
