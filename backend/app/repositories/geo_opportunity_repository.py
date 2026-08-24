from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.geo_prompt_opportunity import (
    GeoPromptOpportunity,
)


class GeoOpportunityRepository:

    @staticmethod
    def clear_experiment(
        db: Session,
        experiment_id: int,
    ) -> None:
        db.execute(
            delete(GeoPromptOpportunity).where(
                GeoPromptOpportunity.experiment_id
                == experiment_id
            )
        )

        db.flush()

    @staticmethod
    def create(
        db: Session,
        **data,
    ) -> GeoPromptOpportunity:

        opportunity = GeoPromptOpportunity(
            **data
        )

        db.add(opportunity)
        db.flush()

        return opportunity

    @staticmethod
    def list_by_experiment(
        db: Session,
        experiment_id: int,
    ) -> list[GeoPromptOpportunity]:

        statement = (
            select(GeoPromptOpportunity)
            .where(
                GeoPromptOpportunity.experiment_id
                == experiment_id
            )
            .order_by(
                GeoPromptOpportunity
                .opportunity_score
                .desc(),
                GeoPromptOpportunity.id,
            )
        )

        return list(
            db.scalars(statement).all()
        )
