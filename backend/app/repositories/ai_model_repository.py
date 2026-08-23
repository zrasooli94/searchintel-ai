from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ai_model import AIModel


class AIModelRepository:

    @staticmethod
    def create(
        db: Session,
        engine_id: int,
        name: str,
        provider_model_id: str,
        is_active: bool,
    ) -> AIModel:
        model = AIModel(
            engine_id=engine_id,
            name=name,
            provider_model_id=provider_model_id,
            is_active=is_active,
        )

        db.add(model)
        db.commit()
        db.refresh(model)

        return model

    @staticmethod
    def get_by_id(
        db: Session,
        model_id: int,
    ) -> AIModel | None:
        return db.get(
            AIModel,
            model_id,
        )

    @staticmethod
    def find_duplicate(
        db: Session,
        engine_id: int,
        provider_model_id: str,
    ) -> AIModel | None:
        statement = select(AIModel).where(
            AIModel.engine_id == engine_id,
            AIModel.provider_model_id == provider_model_id,
        )

        return db.scalar(statement)

    @staticmethod
    def list_by_engine(
        db: Session,
        engine_id: int,
    ) -> list[AIModel]:
        statement = (
            select(AIModel)
            .where(
                AIModel.engine_id == engine_id
            )
            .order_by(AIModel.id)
        )

        return list(
            db.scalars(statement).all()
        )
