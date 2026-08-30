import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ai_run import AIRun
from app.models.geo_experiment import GeoExperiment
from app.repositories.geo_opportunity_repository import GeoOpportunityRepository
from app.repositories.site_rag_gap_analysis_repository import SiteRAGGapAnalysisRepository
from app.services.geo_opportunity_service import GeoOpportunityService
from app.services.site_rag_gap_service import SiteRAGGapService


class MeasurementDerivationService:
    @staticmethod
    def refresh(
        db: Session,
        experiment_id: int,
        benchmark_mode: str,
    ) -> dict | None:
        if benchmark_mode == "web_search":
            return GeoOpportunityService.refresh(db, experiment_id)

        if benchmark_mode == "site_rag":
            return SiteRAGGapService.refresh(db, experiment_id)

        return None

    @classmethod
    def backfill_missing(
        cls,
        db: Session,
        project_id: int | None = None,
    ) -> list[dict]:
        statement = select(GeoExperiment).where(
            GeoExperiment.status == "completed",
        )
        if project_id is not None:
            statement = statement.where(GeoExperiment.project_id == project_id)

        experiments = list(db.scalars(statement.order_by(GeoExperiment.id)).all())
        refreshed = []
        for experiment in experiments:
            modes = set(db.scalars(
                select(AIRun.benchmark_mode)
                .where(
                    AIRun.experiment_id == experiment.id,
                    AIRun.include_in_metrics.is_(True),
                    AIRun.status == "completed",
                )
                .distinct()
            ).all())
            if len(modes) != 1:
                continue

            mode = next(iter(modes))
            if mode == "web_search" and GeoOpportunityRepository.list_by_experiment(
                db, experiment.id
            ):
                continue
            if mode == "site_rag" and (
                SiteRAGGapAnalysisRepository.completed_by_experiment(db, experiment.id)
                is not None
            ):
                continue

            try:
                result = cls.refresh(db, experiment.id, mode)
            except Exception:
                db.rollback()
                logging.getLogger(__name__).exception(
                    "Could not backfill derived analysis for experiment %s.",
                    experiment.id,
                )
                continue
            if result is not None:
                refreshed.append({
                    "experiment_id": experiment.id,
                    "benchmark_mode": mode,
                    "total_prompts": result["total_prompts"],
                })

        return refreshed
