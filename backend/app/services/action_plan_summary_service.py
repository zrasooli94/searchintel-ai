from collections import defaultdict

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ai_run import AIRun
from app.models.brand import Brand

from app.repositories.geo_action_plan_repository import (
    GeoActionPlanRepository,
)
from app.repositories.geo_experiment_repository import (
    GeoExperimentRepository,
)
from app.repositories.project_repository import (
    ProjectRepository,
)
from app.services.site_rag_action_bridge_service import (
    SiteRAGActionBridgeService,
)


class ActionPlanSummaryService:

    @classmethod
    def build(
        cls,
        db: Session,
        project_id: int,
    ) -> dict:

        project = ProjectRepository.get_by_id(
            db,
            project_id,
        )

        if project is None:
            raise HTTPException(
                status_code=404,
                detail="Project not found.",
            )

        site_rag = (
            SiteRAGActionBridgeService.build(
                db=db,
                project_id=project_id,
            )
        )

        plan = (
            GeoActionPlanRepository
            .latest_by_project(
                db,
                project_id,
            )
        )

        if plan is None:
            return {
                "project_id":
                    project_id,

                "has_historical_plan":
                    False,

                "plan_id":
                    None,

                "experiment_id":
                    None,

                "experiment_name":
                    None,

                "experiment_phase":
                    None,

                "experiment_status":
                    None,

                "benchmark_mode":
                    None,

                "target_brand_id":
                    None,

                "target_brand":
                    None,

                "plan_status":
                    None,

                "created_at":
                    None,

                "strategy_summary":
                    None,

                "baseline_metrics":
                    {},

                "recommended_sequence":
                    [],

                "risks_and_limits":
                    [],

                "total_actions":
                    0,

                "open_actions":
                    0,

                "completed_actions":
                    0,

                "high_priority_actions":
                    0,

                "medium_priority_actions":
                    0,

                "low_priority_actions":
                    0,

                "action_type_counts":
                    {},

                "provenance_note":
                    None,

                "site_rag":
                    site_rag,

                "actions":
                    [],
            }

        experiment = (
            GeoExperimentRepository.get(
                db,
                plan.experiment_id,
            )
        )

        if experiment is None:
            raise HTTPException(
                status_code=404,
                detail=(
                    "Source experiment not found."
                ),
            )

        target_brand = db.get(
            Brand,
            plan.target_brand_id,
        )

        if target_brand is None:
            raise HTTPException(
                status_code=404,
                detail="Target brand not found.",
            )

        actions = (
            GeoActionPlanRepository.list_items(
                db,
                plan.id,
            )
        )

        # ---------------------------------------------
        # Determine source experiment mode.
        #
        # Legacy NULL mode means memory.
        # ---------------------------------------------

        mode_rows = list(
            db.scalars(
                select(
                    AIRun.benchmark_mode
                )
                .where(
                    AIRun.experiment_id
                    == experiment.id,

                    AIRun.include_in_metrics
                    .is_(True),
                )
                .distinct()
            ).all()
        )

        benchmark_modes = {
            mode or "memory"
            for mode in mode_rows
        }

        if len(benchmark_modes) == 1:
            benchmark_mode = next(
                iter(benchmark_modes)
            )
        elif len(benchmark_modes) > 1:
            benchmark_mode = "mixed"
        else:
            benchmark_mode = "unknown"

        action_type_counts = defaultdict(
            int
        )

        for action in actions:
            action_type_counts[
                action.action_type
            ] += 1

        def priority_count(
            priority: str,
        ) -> int:
            return sum(
                action.priority == priority
                for action in actions
            )

        def status_count(
            status: str,
        ) -> int:
            return sum(
                action.status == status
                for action in actions
            )

        return {
            "project_id":
                project_id,

            "has_historical_plan":
                True,

            "plan_id":
                plan.id,

            "experiment_id":
                experiment.id,

            "experiment_name":
                experiment.name,

            "experiment_phase":
                experiment.phase,

            "experiment_status":
                experiment.status,

            "benchmark_mode":
                benchmark_mode,

            "target_brand_id":
                target_brand.id,

            "target_brand":
                target_brand.name,

            "plan_status":
                plan.status,

            "created_at":
                plan.created_at,

            "strategy_summary":
                plan.strategy_summary,

            "baseline_metrics":
                plan.baseline_metrics,

            "recommended_sequence":
                plan.recommended_sequence,

            "risks_and_limits":
                plan.risks_and_limits,

            "total_actions":
                len(actions),

            "open_actions":
                status_count("open"),

            "completed_actions":
                status_count("completed"),

            "high_priority_actions":
                priority_count("high"),

            "medium_priority_actions":
                priority_count("medium"),

            "low_priority_actions":
                priority_count("low"),

            "action_type_counts":
                dict(
                    action_type_counts
                ),

            "site_rag":
                site_rag,

            "provenance_note": (
                "This action plan reflects the "
                "evidence and metric snapshot stored "
                "when the plan was generated. It is "
                "not automatically rewritten when "
                "later crawls, experiments, entity "
                "resolution, or website changes occur."
            ),

            "actions": [
                {
                    "id":
                        action.id,

                    "sort_order":
                        action.sort_order,

                    "priority":
                        action.priority,

                    "action_type":
                        action.action_type,

                    "title":
                        action.title,

                    "rationale":
                        action.rationale,

                    "target_page":
                        action.target_page,

                    "impacted_prompt_ids":
                        action.impacted_prompt_ids,

                    "impacted_opportunity_ids":
                        action.impacted_opportunity_ids,

                    "implementation_steps":
                        action.implementation_steps,

                    "evidence":
                        action.evidence,

                    "success_metrics":
                        action.success_metrics,

                    "dependencies":
                        action.dependencies,

                    "effort":
                        action.effort,

                    "status":
                        action.status,
                }
                for action in actions
            ],
        }
