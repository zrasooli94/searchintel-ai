from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.technical_recommendation import (
    TechnicalRecommendation,
)


class TechnicalRecommendationRepository:

    @staticmethod
    def get_by_issue(
        db: Session,
        audit_id: int,
        issue_id: int,
    ) -> TechnicalRecommendation | None:
        statement = select(
            TechnicalRecommendation
        ).where(
            TechnicalRecommendation.audit_id == audit_id,
            TechnicalRecommendation.issue_id == issue_id,
        )

        return db.scalar(statement)

    @staticmethod
    def create(
        db: Session,
        **data,
    ) -> TechnicalRecommendation:
        recommendation = TechnicalRecommendation(
            **data
        )

        db.add(recommendation)
        db.flush()

        return recommendation

    @staticmethod
    def list_by_audit(
        db: Session,
        audit_id: int,
    ) -> list[TechnicalRecommendation]:
        statement = (
            select(TechnicalRecommendation)
            .where(
                TechnicalRecommendation.audit_id == audit_id
            )
            .order_by(
                TechnicalRecommendation.priority_score.desc(),
                TechnicalRecommendation.id,
            )
        )

        return list(
            db.scalars(statement).all()
        )
