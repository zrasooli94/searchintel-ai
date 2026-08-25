from sqlalchemy.orm import Session

from app.repositories.geo_experiment_repository import (
    GeoExperimentRepository,
)
from app.services.visibility_metrics_service import (
    VisibilityMetricsService,
)


class VisibilitySummaryService:

    COVERAGE_THRESHOLD = 50.0
    LEADER_LIMIT = 5

    @classmethod
    def _find_brand_item(
        cls,
        items: list[dict],
        brand_id: int,
    ) -> dict | None:

        for item in items:
            if item.get("brand_id") == brand_id:
                return item

        return None

    @classmethod
    def _normalize_leaders(
        cls,
        items: list[dict],
        exposure_key: str,
        sov_key: str,
        coverage_key: str,
    ) -> list[dict]:

        leaders = []

        for item in items[: cls.LEADER_LIMIT]:

            leaders.append(
                {
                    "brand_id":
                        item["brand_id"],

                    "name":
                        item["name"],

                    "exposures":
                        item.get(
                            exposure_key,
                            0,
                        ),

                    "share_of_voice":
                        item.get(
                            sov_key,
                            0.0,
                        ),

                    "coverage":
                        item.get(
                            coverage_key,
                            0.0,
                        ),
                }
            )

        return leaders

    @classmethod
    def _diagnose(
        cls,
        metrics: dict,
        target_brand: str,
    ) -> dict:

        web_runs = metrics[
            "web_search_analyzed_runs"
        ]

        if web_runs == 0:
            return {
                "primary_bottleneck":
                    "not_applicable",

                "message": (
                    "This experiment has no eligible "
                    "web-search runs, so live-web "
                    "retrieval and citation bottlenecks "
                    "cannot be diagnosed."
                ),

                "rule_version":
                    "visibility_summary_v1",

                "coverage_threshold":
                    cls.COVERAGE_THRESHOLD,
            }

        source_presence = (
            metrics.get(
                "target_source_presence_rate"
            )
            or 0.0
        )

        citation_rate = (
            metrics.get(
                "citation_rate"
            )
            or 0.0
        )

        cited_coverage = (
            metrics.get(
                "target_cited_response_coverage"
            )
            or 0.0
        )

        if source_presence == 0.0:
            bottleneck = "retrieval"

            message = (
                f"{target_brand}'s registered "
                "first-party web evidence was not "
                "retrieved in the measured web-search "
                "responses. Improve discoverability "
                "and retrieval before optimizing for "
                "citation conversion."
            )

        elif citation_rate == 0.0:
            bottleneck = "citation"

            message = (
                f"{target_brand}'s first-party web "
                "evidence was retrieved, but it was "
                "not cited. The primary measured "
                "bottleneck is citation usage."
            )

        elif (
            cited_coverage
            < cls.COVERAGE_THRESHOLD
        ):
            bottleneck = "coverage"

            message = (
                f"{target_brand} is retrieved and "
                "cited, but cited response coverage "
                f"is below the V1 dashboard threshold "
                f"of {cls.COVERAGE_THRESHOLD:.0f}%."
            )

        else:
            bottleneck = "none"

            message = (
                f"{target_brand} has no primary "
                "retrieval, citation, or coverage "
                "bottleneck under the V1 dashboard "
                "rules."
            )

        return {
            "primary_bottleneck":
                bottleneck,

            "message":
                message,

            "rule_version":
                "visibility_summary_v1",

            "coverage_threshold":
                cls.COVERAGE_THRESHOLD,
        }

    @classmethod
    def build(
        cls,
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
            from fastapi import HTTPException

            raise HTTPException(
                status_code=404,
                detail="Experiment not found.",
            )

        # Important:
        # GET summary requests must not create
        # MetricSnapshot rows.
        metrics = (
            VisibilityMetricsService.calculate(
                db=db,
                project_id=experiment.project_id,
                experiment_id=experiment.id,
                persist_snapshot=False,
            )
        )

        target_brand_id = metrics[
            "target_brand_id"
        ]

        target_brand = metrics[
            "target_brand"
        ]

        response_items = metrics.get(
            "response_share_of_voice",
            [],
        )

        retrieval_items = metrics.get(
            "grounded_response_share_of_voice",
            [],
        )

        citation_items = metrics.get(
            "cited_response_share_of_voice",
            [],
        )

        target_response = cls._find_brand_item(
            response_items,
            target_brand_id,
        )

        target_retrieval = cls._find_brand_item(
            retrieval_items,
            target_brand_id,
        )

        target_citation = cls._find_brand_item(
            citation_items,
            target_brand_id,
        )

        mentioned_responses = (
            target_response.get(
                "response_exposures",
                0,
            )
            if target_response
            else 0
        )

        retrieval_associated_responses = (
            target_retrieval.get(
                "grounded_response_exposures",
                0,
            )
            if target_retrieval
            else 0
        )

        cited_responses = (
            target_citation.get(
                "cited_response_exposures",
                0,
            )
            if target_citation
            else 0
        )

        web_runs = metrics[
            "web_search_analyzed_runs"
        ]

        total_responses = (
            web_runs
            if web_runs
            else metrics["analyzed_runs"]
        )

        entity_verified_rate = metrics.get(
            "entity_verified_target_mention_rate"
        )

        entity_verified_responses = (
            round(
                total_responses
                * entity_verified_rate
                / 100.0
            )
            if entity_verified_rate is not None
            else 0
        )


        return {
            "project_id":
                experiment.project_id,

            "experiment_id":
                experiment.id,

            "experiment_name":
                experiment.name,

            "experiment_phase":
                experiment.phase,

            "experiment_status":
                experiment.status,

            "benchmark_mode":
                metrics["benchmark_mode"],

            "analyzed_runs":
                metrics["analyzed_runs"],

            "analyzed_prompts":
                metrics["analyzed_prompts"],

            "target": {
                "brand_id":
                    target_brand_id,

                "brand":
                    target_brand,

                "web_visibility_score":
                    metrics.get(
                        "web_visibility_score_v1"
                    ),

                "raw_response_coverage":
                    metrics[
                        "target_response_coverage"
                    ],

                "entity_verified_response_coverage":
                    metrics.get(
                        "entity_verified_target_mention_rate"
                    ),

                "entity_verified_share_of_voice":
                    metrics.get(
                        "entity_verified_target_share_of_voice"
                    ),


                "source_presence_rate":
                    metrics.get(
                        "target_source_presence_rate"
                    ),

                "retrieval_associated_response_coverage":
                    metrics.get(
                        "grounded_target_mention_rate"
                    ),

                "cited_response_coverage":
                    metrics.get(
                        "target_cited_response_coverage"
                    ),

                "response_share_of_voice":
                    metrics[
                        "target_response_share_of_voice"
                    ],

                "retrieval_associated_response_share_of_voice":
                    metrics.get(
                        "target_grounded_response_share_of_voice"
                    ),

                "cited_response_share_of_voice":
                    metrics.get(
                        "target_cited_response_share_of_voice"
                    ),

                "source_exposure_share_of_voice":
                    metrics.get(
                        "target_source_exposure_share_of_voice"
                    ),

                "citation_exposure_share_of_voice":
                    metrics.get(
                        "target_citation_exposure_share_of_voice"
                    ),

                "citation_exposure_conversion":
                    metrics.get(
                        "target_citation_exposure_conversion"
                    ),
            },

            "funnel": {
                "total_responses":
                    total_responses,

                "mentioned_responses":
                    mentioned_responses,

                "entity_verified_responses":
                    entity_verified_responses,


                "retrieval_associated_responses":
                    retrieval_associated_responses,

                "cited_responses":
                    cited_responses,
            },

            "leaders": {
                "response_visibility":
                    cls._normalize_leaders(
                        response_items,
                        "response_exposures",
                        "response_share_of_voice",
                        "response_coverage",
                    ),

                "retrieval_visibility":
                    cls._normalize_leaders(
                        retrieval_items,
                        "grounded_response_exposures",
                        "grounded_response_share_of_voice",
                        "grounded_response_coverage",
                    ),

                "citation_visibility":
                    cls._normalize_leaders(
                        citation_items,
                        "cited_response_exposures",
                        "cited_response_share_of_voice",
                        "cited_response_coverage",
                    ),
            },

            "diagnosis":
                cls._diagnose(
                    metrics,
                    target_brand,
                ),
        }
