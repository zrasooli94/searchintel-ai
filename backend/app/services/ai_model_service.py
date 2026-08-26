from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.ai_model import AIModel
from app.models.ai_run import AIRun
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
            provider_model_id=
                data.provider_model_id.strip(),
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

    @staticmethod
    def resolve_execution_model(
        db: Session,
        model_id: int | None,
    ) -> AIModel:
        if model_id is not None:
            model = AIModelRepository.get_by_id(
                db,
                model_id,
            )

            if model is None:
                raise HTTPException(
                    status_code=404,
                    detail="AI model not found.",
                )

            if not model.is_active:
                raise HTTPException(
                    status_code=400,
                    detail="AI model is inactive.",
                )

            if (
                not model.provider_model_id
                or model.provider_model_id
                == "configure-later"
            ):
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Selected AI model is not "
                        "configured for provider use."
                    ),
                )

            return model

        # Prefer a configured active model that
        # already has successful SearchIntel runs.
        statement = (
            select(
                AIModel,
                func.count(
                    AIRun.id
                ).label("run_count"),
            )
            .join(
                AIRun,
                AIRun.model_id == AIModel.id,
            )
            .where(
                AIModel.is_active.is_(True),
                AIModel.provider_model_id
                != "configure-later",
                AIRun.status == "completed",
            )
            .group_by(
                AIModel.id,
            )
            .order_by(
                func.count(
                    AIRun.id
                ).desc(),
                AIModel.id.desc(),
            )
            .limit(1)
        )

        row = db.execute(
            statement
        ).first()

        if row is not None:
            return row[0]

        # Fallback to the newest configured active
        # OpenAI model.
        engine = AIEngineRepository.get_by_slug(
            db,
            "openai",
        )

        if engine is None:
            raise HTTPException(
                status_code=400,
                detail=(
                    "No supported AI engine "
                    "is configured."
                ),
            )

        candidates = (
            AIModelRepository.list_by_engine(
                db,
                engine.id,
            )
        )

        candidates = [
            model
            for model in candidates
            if (
                model.is_active
                and model.provider_model_id
                and model.provider_model_id
                != "configure-later"
            )
        ]

        if not candidates:
            raise HTTPException(
                status_code=400,
                detail=(
                    "No active configured AI "
                    "model is available."
                ),
            )

        return sorted(
            candidates,
            key=lambda model: model.id,
            reverse=True,
        )[0]
