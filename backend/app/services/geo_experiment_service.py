from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ai_run import AIRun
from app.repositories.geo_experiment_repository import (
    GeoExperimentRepository,
)
from app.repositories.project_repository import (
    ProjectRepository,
)


class GeoExperimentService:

    VALID_PHASES = {
        "baseline",
        "optimization",
        "validation",
        "monitoring",
    }

    @classmethod
    def create(
        cls,
        db: Session,
        project_id: int,
        name: str,
        phase: str,
        description: str | None,
    ):
        project = ProjectRepository.get_by_id(
            db,
            project_id,
        )

        if project is None:
            raise HTTPException(
                status_code=404,
                detail="Project not found.",
            )

        name = name.strip()
        phase = phase.strip().lower()

        if len(name) < 2:
            raise HTTPException(
                status_code=400,
                detail="Experiment name is too short.",
            )

        if phase not in cls.VALID_PHASES:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Invalid experiment phase."
                ),
            )

        existing = (
            GeoExperimentRepository.get_by_name(
                db,
                project_id,
                name,
            )
        )

        if existing:
            raise HTTPException(
                status_code=409,
                detail=(
                    "Experiment name already exists "
                    "for this project."
                ),
            )

        experiment = (
            GeoExperimentRepository.create(
                db=db,
                project_id=project_id,
                name=name,
                phase=phase,
                description=description,
            )
        )

        db.commit()
        db.refresh(experiment)

        return experiment

    @staticmethod
    def list(
        db: Session,
        project_id: int,
    ):
        project = ProjectRepository.get_by_id(
            db,
            project_id,
        )

        if project is None:
            raise HTTPException(
                status_code=404,
                detail="Project not found.",
            )

        return (
            GeoExperimentRepository.list_by_project(
                db,
                project_id,
            )
        )

    @staticmethod
    def adopt_unassigned_runs(
        db: Session,
        experiment_id: int,
    ) -> dict:
        experiment = (
            GeoExperimentRepository.get(
                db,
                experiment_id,
            )
        )

        if experiment is None:
            raise HTTPException(
                status_code=404,
                detail="Experiment not found.",
            )

        statement = (
            select(AIRun)
            .where(
                AIRun.project_id
                == experiment.project_id,
                AIRun.include_in_metrics.is_(True),
                AIRun.status == "completed",
                AIRun.experiment_id.is_(None),
            )
            .order_by(AIRun.id)
        )

        runs = list(
            db.scalars(statement).all()
        )

        for run in runs:
            run.experiment_id = experiment.id

        if runs:
            timestamps = [
                run.started_at
                for run in runs
                if run.started_at is not None
            ]

            experiment.started_at = (
                min(timestamps)
                if timestamps
                else datetime.now(timezone.utc)
            )

            experiment.completed_at = datetime.now(
                timezone.utc
            )

            experiment.status = "completed"

        db.commit()

        return {
            "experiment_id":
                experiment.id,
            "project_id":
                experiment.project_id,
            "adopted_runs":
                len(runs),
        }
