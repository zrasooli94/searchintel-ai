from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.analysis_versions import (
    VISIBILITY_ANALYSIS_VERSION,
)
from app.models.ai_response import AIResponse
from app.models.ai_run import AIRun
from app.models.geo_experiment import GeoExperiment
from app.services.visibility_analysis_service import (
    VisibilityAnalysisService,
)


class ExperimentReanalysisService:

    @staticmethod
    def response_versions(
        db: Session,
        project_id: int,
        experiment_id: int,
    ):
        statement = (
            select(
                AIRun.id.label("run_id"),
                AIResponse.visibility_analysis_version,
            )
            .join(
                AIResponse,
                AIResponse.run_id == AIRun.id,
            )
            .where(
                AIRun.project_id == project_id,
                AIRun.experiment_id == experiment_id,
                AIRun.include_in_metrics.is_(True),
                AIRun.status == "completed",
            )
            .order_by(AIRun.id)
        )

        return list(
            db.execute(statement).all()
        )

    @classmethod
    def reanalyze(
        cls,
        db: Session,
        project_id: int,
        experiment_id: int,
    ) -> dict:
        experiment = db.get(
            GeoExperiment,
            experiment_id,
        )

        if (
            experiment is None
            or experiment.project_id
            != project_id
        ):
            raise HTTPException(
                status_code=404,
                detail="Experiment not found.",
            )

        before = cls.response_versions(
            db=db,
            project_id=project_id,
            experiment_id=experiment_id,
        )

        stale_run_ids = [
            row.run_id
            for row in before
            if (
                row.visibility_analysis_version
                != VISIBILITY_ANALYSIS_VERSION
            )
        ]

        failed_run_ids: list[int] = []
        reanalyzed = 0

        for run_id in stale_run_ids:
            try:
                VisibilityAnalysisService.analyze(
                    db,
                    run_id,
                )

                reanalyzed += 1

            except Exception:
                db.rollback()
                failed_run_ids.append(
                    run_id
                )

        after = cls.response_versions(
            db=db,
            project_id=project_id,
            experiment_id=experiment_id,
        )

        current_after = sum(
            1
            for row in after
            if (
                row.visibility_analysis_version
                == VISIBILITY_ANALYSIS_VERSION
            )
        )

        stale_after = (
            len(after)
            - current_after
        )

        return {
            "project_id":
                project_id,

            "experiment_id":
                experiment_id,

            "analysis_version":
                VISIBILITY_ANALYSIS_VERSION,

            "total_responses":
                len(before),

            "stale_before":
                len(stale_run_ids),

            "skipped_current":
                len(before)
                - len(stale_run_ids),

            "reanalyzed":
                reanalyzed,

            "failed":
                len(failed_run_ids),

            "failed_run_ids":
                failed_run_ids,

            "current_after":
                current_after,

            "stale_after":
                stale_after,

            "analysis_is_current":
                len(after) > 0
                and stale_after == 0,
        }
