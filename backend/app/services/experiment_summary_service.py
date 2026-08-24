from collections import defaultdict

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ai_run import AIRun
from app.repositories.geo_experiment_repository import (
    GeoExperimentRepository,
)
from app.services.visibility_metrics_service import (
    VisibilityMetricsService,
)


class ExperimentSummaryService:

    @classmethod
    def build(
        cls,
        db: Session,
        project_id: int,
    ) -> dict:

        experiments = (
            GeoExperimentRepository.list_by_project(
                db,
                project_id,
            )
        )

        if not experiments:
            raise HTTPException(
                status_code=404,
                detail="Project has no experiments.",
            )

        experiment_ids = [
            experiment.id
            for experiment in experiments
        ]

        run_rows = list(
            db.execute(
                select(
                    AIRun.experiment_id,
                    AIRun.id,
                    AIRun.prompt_id,
                )
                .where(
                    AIRun.experiment_id.in_(
                        experiment_ids
                    ),
                    AIRun.include_in_metrics
                    .is_(True),
                )
            ).all()
        )

        runs_by_experiment = defaultdict(set)
        prompts_by_experiment = defaultdict(set)

        for row in run_rows:
            runs_by_experiment[
                row.experiment_id
            ].add(
                row.id
            )

            prompts_by_experiment[
                row.experiment_id
            ].add(
                row.prompt_id
            )

        items = []

        for experiment in experiments:

            metrics = (
                VisibilityMetricsService.calculate(
                    db=db,
                    project_id=project_id,
                    experiment_id=experiment.id,
                    persist_snapshot=False,
                )
            )

            items.append(
                {
                    "id":
                        experiment.id,

                    "name":
                        experiment.name,

                    "phase":
                        experiment.phase,

                    "status":
                        experiment.status,

                    "benchmark_mode":
                        metrics[
                            "benchmark_mode"
                        ],

                    "runs":
                        len(
                            runs_by_experiment[
                                experiment.id
                            ]
                        ),

                    "prompts":
                        len(
                            prompts_by_experiment[
                                experiment.id
                            ]
                        ),

                    "mention_rate":
                        metrics[
                            "mention_rate"
                        ],

                    "prompt_coverage":
                        metrics[
                            "prompt_coverage"
                        ],

                    "citation_rate":
                        metrics[
                            "citation_rate"
                        ],

                    "visibility_score_v1":
                        metrics[
                            "visibility_score_v1"
                        ],

                    "web_visibility_score_v1":
                        metrics.get(
                            "web_visibility_score_v1"
                        ),

                    "target_response_coverage":
                        metrics[
                            "target_response_coverage"
                        ],

                    "grounded_target_mention_rate":
                        metrics.get(
                            "grounded_target_mention_rate"
                        ),

                    "target_cited_response_coverage":
                        metrics.get(
                            "target_cited_response_coverage"
                        ),

                    "target_source_presence_rate":
                        metrics.get(
                            "target_source_presence_rate"
                        ),

                    "started_at":
                        experiment.started_at,

                    "completed_at":
                        experiment.completed_at,

                    "created_at":
                        experiment.created_at,
                }
            )

        comparable_pairs = []

        for baseline in items:
            for comparison in items:

                if (
                    baseline["id"]
                    >= comparison["id"]
                ):
                    continue

                if (
                    baseline["benchmark_mode"]
                    != comparison[
                        "benchmark_mode"
                    ]
                ):
                    continue

                comparable_pairs.append(
                    {
                        "baseline_id":
                            baseline["id"],

                        "baseline_name":
                            baseline["name"],

                        "comparison_id":
                            comparison["id"],

                        "comparison_name":
                            comparison["name"],

                        "benchmark_mode":
                            baseline[
                                "benchmark_mode"
                            ],
                    }
                )

        return {
            "project_id":
                project_id,

            "total_experiments":
                len(items),

            "completed_experiments":
                sum(
                    item["status"]
                    == "completed"
                    for item in items
                ),

            "draft_experiments":
                sum(
                    item["status"]
                    == "draft"
                    for item in items
                ),

            "experiments":
                items,

            "comparable_pairs":
                comparable_pairs,
        }
