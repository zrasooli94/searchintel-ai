from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.site_rag_gap import SiteRAGGap


class SiteRAGGapRepository:

    @staticmethod
    def clear_experiment(
        db: Session,
        experiment_id: int,
    ) -> None:
        db.execute(
            delete(SiteRAGGap).where(
                SiteRAGGap.experiment_id
                == experiment_id
            )
        )

        db.flush()

    @staticmethod
    def create(
        db: Session,
        **data,
    ) -> SiteRAGGap:
        record = SiteRAGGap(
            **data
        )

        db.add(record)
        db.flush()

        return record

    @staticmethod
    def list_by_experiment(
        db: Session,
        experiment_id: int,
    ) -> list[SiteRAGGap]:
        statement = (
            select(SiteRAGGap)
            .where(
                SiteRAGGap.experiment_id
                == experiment_id
            )
            .order_by(
                SiteRAGGap.gap_score.desc(),
                SiteRAGGap.id,
            )
        )

        return list(
            db.scalars(statement).all()
        )
