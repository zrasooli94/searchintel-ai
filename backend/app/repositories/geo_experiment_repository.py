from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.geo_experiment import GeoExperiment


class GeoExperimentRepository:

    @staticmethod
    def create(
        db: Session,
        project_id: int,
        name: str,
        phase: str,
        description: str | None,
    ) -> GeoExperiment:

        experiment = GeoExperiment(
            project_id=project_id,
            name=name,
            phase=phase,
            status="draft",
            description=description,
        )

        db.add(experiment)
        db.flush()

        return experiment

    @staticmethod
    def get(
        db: Session,
        experiment_id: int,
    ) -> GeoExperiment | None:
        return db.get(
            GeoExperiment,
            experiment_id,
        )

    @staticmethod
    def get_by_name(
        db: Session,
        project_id: int,
        name: str,
    ) -> GeoExperiment | None:
        statement = select(
            GeoExperiment
        ).where(
            GeoExperiment.project_id == project_id,
            GeoExperiment.name == name,
        )

        return db.scalar(statement)

    @staticmethod
    def list_by_project(
        db: Session,
        project_id: int,
    ) -> list[GeoExperiment]:
        statement = (
            select(GeoExperiment)
            .where(
                GeoExperiment.project_id
                == project_id
            )
            .order_by(
                GeoExperiment.id
            )
        )

        return list(
            db.scalars(statement).all()
        )
