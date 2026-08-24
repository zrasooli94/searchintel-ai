from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.repositories.geo_experiment_repository import (
    GeoExperimentRepository,
)
from app.services.visibility_metrics_service import (
    VisibilityMetricsService,
)


class ExperimentComparisonService:

    @staticmethod
    def metric(
        baseline: float | None,
        comparison: float | None,
    ) -> dict:

        delta = None

        if (
            baseline is not None
            and comparison is not None
        ):
            delta = round(
                comparison - baseline,
                2,
            )

        return {
            "baseline": baseline,
            "comparison": comparison,
            "delta": delta,
        }

    @classmethod
    def compare(
        cls,
        db: Session,
        project_id: int,
        baseline_id: int,
        comparison_id: int,
    ) -> dict:

        baseline_experiment = (
            GeoExperimentRepository.get(
                db,
                baseline_id,
            )
        )

        comparison_experiment = (
            GeoExperimentRepository.get(
                db,
                comparison_id,
            )
        )

        if (
            baseline_experiment is None
            or comparison_experiment is None
        ):
            raise HTTPException(
                status_code=404,
                detail="Experiment not found.",
            )

        if (
            baseline_experiment.project_id
            != project_id
            or comparison_experiment.project_id
            != project_id
        ):
            raise HTTPException(
                status_code=400,
                detail=(
                    "Both experiments must belong "
                    "to this project."
                ),
            )

        baseline = (
            VisibilityMetricsService.calculate(
                db=db,
                project_id=project_id,
                experiment_id=baseline_id,
                persist_snapshot=False,
            )
        )

        comparison = (
            VisibilityMetricsService.calculate(
                db=db,
                project_id=project_id,
                experiment_id=comparison_id,
                persist_snapshot=False,
            )
        )

        return {
            "project_id": project_id,

            "baseline_experiment_id":
                baseline_id,

            "comparison_experiment_id":
                comparison_id,

            "baseline_name":
                baseline_experiment.name,

            "comparison_name":
                comparison_experiment.name,

            "baseline_runs":
                baseline["analyzed_runs"],

            "comparison_runs":
                comparison["analyzed_runs"],

            "mention_rate":
                cls.metric(
                    baseline["mention_rate"],
                    comparison["mention_rate"],
                ),

            "prompt_coverage":
                cls.metric(
                    baseline["prompt_coverage"],
                    comparison["prompt_coverage"],
                ),

            "citation_rate":
                cls.metric(
                    baseline["citation_rate"],
                    comparison["citation_rate"],
                ),

            "target_share_of_voice":
                cls.metric(
                    baseline[
                        "target_share_of_voice"
                    ],
                    comparison[
                        "target_share_of_voice"
                    ],
                ),

            "visibility_score_v1":
                cls.metric(
                    baseline[
                        "visibility_score_v1"
                    ],
                    comparison[
                        "visibility_score_v1"
                    ],
                ),

            "average_mention_position":
                cls.metric(
                    baseline[
                        "average_mention_position"
                    ],
                    comparison[
                        "average_mention_position"
                    ],
                ),
        }
