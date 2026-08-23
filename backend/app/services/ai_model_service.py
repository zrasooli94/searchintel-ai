from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.ai_model import AIModel
from app.repositories.ai_engine_repository import (
    AIEngineRepository,
)
from app.repositories.ai_model_repository import (
    AIModelRepository,
)
from app.schemas.ai_model import AIModelCreate


class AIModelService:

    @staticmethod
    def create(
        db: Session,
        engine_id: int,
        data: AIModelCreate,
    ) -> AIModel:
        engine = AIEngineRepository.get_by_id(
            db,
            engine_id,
        )

        if engine is None:
            raise HTTPException(
                status_code=404,
                detail="AI engine not found.",
            )

        existing = AIModelRepository.find_duplicate(
            db,
            engine_id,
            data.provider_model_id,
        )

        if existing:
            raise HTTPException(
                status_code=409,
                detail="AI model already exists.",
            )

        return AIModelRepository.create(
            db=db,
            engine_id=engine_id,
            name=data.name.strip(),
            provider_model_id=data.provider_model_id.strip(),
            is_active=data.is_active,
        )

    @staticmethod
    def list_by_engine(
        db: Session,
        engine_id: int,
    ) -> list[AIModel]:
        engine = AIEngineRepository.get_by_id(
            db,
            engine_id,
        )

        if engine is None:
            raise HTTPException(
                status_code=404,
                detail="AI engine not found.",
            )

        return AIModelRepository.list_by_engine(
            db,
            engine_id,
        )
