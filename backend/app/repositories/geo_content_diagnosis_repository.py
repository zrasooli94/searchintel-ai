from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.geo_content_diagnosis import (
    GeoContentDiagnosis,
)


class GeoContentDiagnosisRepository:

    @staticmethod
    def create(
        db: Session,
        **data,
    ) -> GeoContentDiagnosis:

        diagnosis = GeoContentDiagnosis(
            **data
        )

        db.add(diagnosis)
        db.flush()

        return diagnosis

    @staticmethod
    def latest(
        db: Session,
        opportunity_id: int,
    ) -> GeoContentDiagnosis | None:

        statement = (
            select(GeoContentDiagnosis)
            .where(
                GeoContentDiagnosis.opportunity_id
                == opportunity_id
            )
            .order_by(
                GeoContentDiagnosis.created_at.desc(),
                GeoContentDiagnosis.id.desc(),
            )
            .limit(1)
        )

        return db.scalar(statement)
