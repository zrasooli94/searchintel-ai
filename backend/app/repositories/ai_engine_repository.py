from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ai_engine import AIEngine


class AIEngineRepository:

    @staticmethod
    def create(
        db: Session,
        name: str,
        slug: str,
    ) -> AIEngine:
        engine = AIEngine(
            name=name,
            slug=slug,
        )

        db.add(engine)
        db.commit()
        db.refresh(engine)

        return engine

    @staticmethod
    def get_by_id(
        db: Session,
        engine_id: int,
    ) -> AIEngine | None:
        return db.get(
            AIEngine,
            engine_id,
        )

    @staticmethod
    def get_by_slug(
        db: Session,
        slug: str,
    ) -> AIEngine | None:
        statement = select(AIEngine).where(
            AIEngine.slug == slug
        )

        return db.scalar(statement)

    @staticmethod
    def list_all(
        db: Session,
    ) -> list[AIEngine]:
        statement = select(
            AIEngine
        ).order_by(
            AIEngine.id
        )

        return list(
            db.scalars(statement).all()
        )
