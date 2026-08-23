import re

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.ai_engine import AIEngine
from app.repositories.ai_engine_repository import (
    AIEngineRepository,
)
from app.schemas.ai_engine import AIEngineCreate


class AIEngineService:

    @staticmethod
    def normalize_slug(
        value: str,
    ) -> str:
        value = value.strip().lower()
        value = re.sub(
            r"[^a-z0-9]+",
            "-",
            value,
        )

        return value.strip("-")

    @classmethod
    def create(
        cls,
        db: Session,
        data: AIEngineCreate,
    ) -> AIEngine:
        name = data.name.strip()
        slug = cls.normalize_slug(
            data.slug
        )

        existing = AIEngineRepository.get_by_slug(
            db,
            slug,
        )

        if existing:
            raise HTTPException(
                status_code=409,
                detail="AI engine already exists.",
            )

        return AIEngineRepository.create(
            db=db,
            name=name,
            slug=slug,
        )

    @staticmethod
    def list_all(
        db: Session,
    ) -> list[AIEngine]:
        return AIEngineRepository.list_all(
            db
        )
