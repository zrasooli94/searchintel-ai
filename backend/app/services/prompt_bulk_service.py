import re

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.prompt import Prompt

from app.repositories.project_repository import (
    ProjectRepository,
)


class PromptBulkService:

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
    def create(
        cls,
        db: Session,
        project_id: int,
        data,
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

        existing = list(
            db.scalars(
                select(Prompt)
                .where(
                    Prompt.project_id
                    == project_id
                )
            ).all()
        )

        existing_texts = {
            cls.normalize_text(
                prompt.text
            )
            for prompt in existing
        }

        request_seen = set()

        created_ids = []
        skipped = 0

        try:
            for item in data.prompts:

                text = re.sub(
                    r"\s+",
                    " ",
                    item.text.strip(),
                )

                normalized = (
                    cls.normalize_text(
                        text
                    )
                )

                if (
                    normalized
                    in existing_texts
                    or normalized
                    in request_seen
                ):
                    skipped += 1
                    continue

                prompt = Prompt(
                    project_id=project_id,
                    text=text,
                    category=item.category,
                    intent=(
                        item.intent.strip()
                        if item.intent
                        else None
                    ),
                    is_active=True,
                )

                db.add(prompt)
                db.flush()

                created_ids.append(
                    prompt.id
                )

                request_seen.add(
                    normalized
                )

            db.commit()

        except Exception:
            db.rollback()
            raise

        return {
            "project_id":
                project_id,

            "requested":
                len(data.prompts),

            "created":
                len(created_ids),

            "skipped_duplicates":
                skipped,

            "created_prompt_ids":
                created_ids,
        }
