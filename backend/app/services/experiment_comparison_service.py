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

        if (
            baseline.get("benchmark_mode")
            != comparison.get("benchmark_mode")
        ):
            raise HTTPException(
                status_code=400,
                detail=(
                    "Experiments with different "
                    "benchmark modes cannot be "
                    "directly compared."
                ),
            )

        def compare_metric(
            name: str,
        ) -> dict:
            return cls.metric(
                baseline.get(name),
                comparison.get(name),
            )

        return {
            "project_id":
                project_id,

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
                compare_metric(
                    "mention_rate"
                ),

            "prompt_coverage":
                compare_metric(
                    "prompt_coverage"
                ),

            "entity_verified_target_mention_rate":
                compare_metric(
                    "entity_verified_target_mention_rate"
                ),

            "entity_verified_target_prompt_coverage":
                compare_metric(
                    "entity_verified_target_prompt_coverage"
                ),

            "entity_verified_target_share_of_voice":
                compare_metric(
                    "entity_verified_target_share_of_voice"
                ),


            "citation_rate":
                compare_metric(
                    "citation_rate"
                ),

            "target_share_of_voice":
                compare_metric(
                    "target_share_of_voice"
                ),

            "visibility_score_v1":
                compare_metric(
                    "visibility_score_v1"
                ),

            "average_mention_position":
                compare_metric(
                    "average_mention_position"
                ),

            "target_source_presence_rate":
                compare_metric(
                    "target_source_presence_rate"
                ),

            "target_source_prompt_coverage":
                compare_metric(
                    "target_source_prompt_coverage"
                ),

            "grounded_target_mention_rate":
                compare_metric(
                    "grounded_target_mention_rate"
                ),

            "grounded_target_prompt_coverage":
                compare_metric(
                    "grounded_target_prompt_coverage"
                ),

            "source_to_citation_conversion":
                compare_metric(
                    "source_to_citation_conversion"
                ),

            "target_source_to_citation_conversion":
                compare_metric(
                    "target_source_to_citation_conversion"
                ),

            "target_source_share_of_voice":
                compare_metric(
                    "target_source_share_of_voice"
                ),

            "target_citation_share_of_voice":
                compare_metric(
                    "target_citation_share_of_voice"
                ),

            "resolved_first_party_source_rate":
                compare_metric(
                    "resolved_first_party_source_rate"
                ),
        }
