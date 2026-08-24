import json
import re

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.integrations.ai.provider_factory import (
    ProviderFactory,
)
from app.repositories.ai_engine_repository import (
    AIEngineRepository,
)
from app.repositories.ai_model_repository import (
    AIModelRepository,
)
from app.repositories.geo_action_plan_repository import (
    GeoActionPlanRepository,
)
from app.repositories.geo_content_diagnosis_repository import (
    GeoContentDiagnosisRepository,
)
from app.repositories.geo_experiment_repository import (
    GeoExperimentRepository,
)
from app.repositories.geo_opportunity_repository import (
    GeoOpportunityRepository,
)
from app.repositories.project_brand_repository import (
    ProjectBrandRepository,
)
from app.services.visibility_metrics_service import (
    VisibilityMetricsService,
)


class GeoActionPlanService:

    VALID_PRIORITIES = {
        "high",
        "medium",
        "low",
    }

    @staticmethod
    def parse_json(
        value: str,
    ) -> dict:

        value = value.strip()

        value = re.sub(
            r"^```(?:json)?\s*",
            "",
            value,
            flags=re.IGNORECASE,
        )

        value = re.sub(
            r"\s*```$",
            "",
            value,
        )

        start = value.find("{")
        end = value.rfind("}")

        if start == -1 or end == -1:
            raise ValueError(
                "Action planner did not return JSON."
            )

        return json.loads(
            value[start:end + 1]
        )

    @classmethod
    def generate(
        cls,
        db: Session,
        experiment_id: int,
        model_id: int,
        priorities: list[str],
        max_actions: int,
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

        model = AIModelRepository.get_by_id(
            db,
            model_id,
        )

        if model is None:
            raise HTTPException(
                status_code=404,
                detail="AI model not found.",
            )

        engine = AIEngineRepository.get_by_id(
            db,
            model.engine_id,
        )

        if engine is None:
            raise HTTPException(
                status_code=404,
                detail="AI engine not found.",
            )

        selected_priorities = {
            item.strip().lower()
            for item in priorities
        }

        invalid = (
            selected_priorities
            - cls.VALID_PRIORITIES
        )

        if invalid:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Invalid priorities: "
                    + ", ".join(sorted(invalid))
                ),
            )

        project_brands = (
            ProjectBrandRepository.list_brand_roles(
                db,
                experiment.project_id,
            )
        )

        target_rows = [
            brand
            for brand, role
            in project_brands
            if role == "target"
        ]

        if not target_rows:
            raise HTTPException(
                status_code=400,
                detail="Target brand not found.",
            )

        target = target_rows[0]

        opportunities = (
            GeoOpportunityRepository
            .list_by_experiment(
                db,
                experiment_id,
            )
        )

        selected = [
            opportunity
            for opportunity in opportunities
            if opportunity.priority
            in selected_priorities
        ]

        diagnosis_payload = []
        diagnosis_ids = []

        valid_prompt_ids = set()
        valid_opportunity_ids = set()

        for opportunity in selected:

            diagnosis = (
                GeoContentDiagnosisRepository.latest(
                    db,
                    opportunity.id,
                )
            )

            if diagnosis is None:
                continue

            diagnosis_ids.append(
                diagnosis.id
            )

            valid_prompt_ids.add(
                opportunity.prompt_id
            )

            valid_opportunity_ids.add(
                opportunity.id
            )

            analysis = diagnosis.analysis or {}

            diagnosis_payload.append(
                {
                    "diagnosis_id":
                        diagnosis.id,

                    "opportunity_id":
                        opportunity.id,

                    "prompt_id":
                        opportunity.prompt_id,

                    "prompt":
                        opportunity.prompt_text,

                    "priority":
                        opportunity.priority,

                    "gap_type":
                        opportunity.gap_type,

                    "opportunity_score":
                        opportunity.opportunity_score,

                    "top_competitor":
                        opportunity.top_competitor_name,

                    "diagnosis_summary":
                        analysis.get(
                            "diagnosis_summary"
                        ),

                    "content_gaps":
                        analysis.get(
                            "content_gaps",
                            [],
                        ),

                    "entity_gaps":
                        analysis.get(
                            "entity_gaps",
                            [],
                        ),

                    "proof_gaps":
                        analysis.get(
                            "proof_gaps",
                            [],
                        ),

                    "recommended_page":
                        analysis.get(
                            "recommended_page",
                            {},
                        ),

                    "on_page_actions":
                        analysis.get(
                            "on_page_actions",
                            [],
                        ),

                    "internal_link_actions":
                        analysis.get(
                            "internal_link_actions",
                            [],
                        ),

                    "structured_data_actions":
                        analysis.get(
                            "structured_data_actions",
                            [],
                        ),

                    "authority_actions":
                        analysis.get(
                            "authority_actions",
                            [],
                        ),

                    "measurement_plan":
                        analysis.get(
                            "measurement_plan",
                            [],
                        ),

                    "limitations":
                        analysis.get(
                            "evidence_limitations",
                            [],
                        ),
                }
            )

        if not diagnosis_payload:
            raise HTTPException(
                status_code=400,
                detail=(
                    "No diagnoses exist for the "
                    "selected opportunities."
                ),
            )

        baseline = (
            VisibilityMetricsService.calculate(
                db=db,
                project_id=experiment.project_id,
                experiment_id=experiment_id,
                persist_snapshot=False,
            )
        )

        baseline_summary = {
            "analyzed_runs":
                baseline["analyzed_runs"],

            "analyzed_prompts":
                baseline["analyzed_prompts"],

            "mention_rate":
                baseline["mention_rate"],

            "prompt_coverage":
                baseline["prompt_coverage"],

            "citation_rate":
                baseline["citation_rate"],

            "target_share_of_voice":
                baseline["target_share_of_voice"],

            "visibility_score_v1":
                baseline["visibility_score_v1"],
        }

        evidence_payload = {
            "target_brand":
                target.name,

            "experiment":
                {
                    "id":
                        experiment.id,
                    "name":
                        experiment.name,
                    "phase":
                        experiment.phase,
                },

            "baseline_metrics":
                baseline_summary,

            "diagnoses":
                diagnosis_payload,
        }

        instructions = f"""
You are the GEO strategy planner for
SearchIntel AI.

Convert the supplied evidence-grounded prompt
diagnoses into a SMALL, CONSOLIDATED,
IMPLEMENTABLE action plan.

The target is NOT one page per prompt.

Combine overlapping diagnoses into shared
actions that can improve multiple prompts.

Return at most {max_actions} actions.

STRICT RULES:

1. Use only supplied evidence.
2. Do not invent customer results, integrations,
   support, certifications, market position,
   statistics, or competitor website facts.
3. Where information needs verification, say
   "verify and document if supported".
4. Prefer actions that address several high
   priority prompts at once.
5. Separate product positioning, content,
   entity clarity, proof, technical/on-page,
   authority, and measurement when appropriate.
6. Every action must reference the supplied
   prompt IDs and opportunity IDs it addresses.
7. Do not promise that a change will cause an
   AI model to mention the brand.
8. Success metrics must be measurable using the
   SearchIntel experiment framework.
9. Keep the plan implementable by a real
   engineering/marketing team.
10. Avoid duplicate actions.

Return ONLY JSON:

{{
  "strategy_summary": "...",

  "recommended_sequence": [
    "..."
  ],

  "actions": [
    {{
      "priority": "high",
      "action_type": "positioning",
      "title": "...",
      "rationale": "...",
      "target_page": "...",

      "impacted_prompt_ids": [1, 2],
      "impacted_opportunity_ids": [1, 2],

      "implementation_steps": [
        "..."
      ],

      "evidence": [
        "..."
      ],

      "success_metrics": [
        "..."
      ],

      "dependencies": [
        "..."
      ],

      "effort": "medium"
    }}
  ],

  "risks_and_limits": [
    "..."
  ]
}}
"""

        prompt = (
            instructions
            + "\n\nEVIDENCE:\n"
            + json.dumps(
                evidence_payload,
                ensure_ascii=False,
                indent=2,
            )
        )

        try:
            provider = ProviderFactory.create(
                engine.slug
            )

            result = provider.execute(
                prompt=prompt,
                model_id=model.provider_model_id,
            )

            payload = cls.parse_json(
                result.response_text
            )

        except Exception as exc:
            raise HTTPException(
                status_code=502,
                detail=(
                    "GEO action planning failed: "
                    f"{exc}"
                ),
            ) from exc

        strategy_summary = str(
            payload.get(
                "strategy_summary",
                "",
            )
        ).strip()

        if not strategy_summary:
            strategy_summary = (
                "Prioritized GEO optimization plan."
            )

        recommended_sequence = (
            payload.get(
                "recommended_sequence",
                [],
            )
        )

        risks_and_limits = (
            payload.get(
                "risks_and_limits",
                [],
            )
        )

        plan = (
            GeoActionPlanRepository.create_plan(
                db=db,
                experiment_id=
                    experiment.id,
                project_id=
                    experiment.project_id,
                target_brand_id=
                    target.id,
                model_id=
                    model.id,
                status="completed",
                strategy_summary=
                    strategy_summary,
                baseline_metrics=
                    baseline_summary,
                source_diagnosis_ids=
                    diagnosis_ids,
                recommended_sequence=
                    recommended_sequence,
                risks_and_limits=
                    risks_and_limits,
            )
        )

        actions = payload.get(
            "actions",
            [],
        )[:max_actions]

        for index, action in enumerate(
            actions,
            start=1,
        ):

            prompt_ids = [
                int(value)
                for value
                in action.get(
                    "impacted_prompt_ids",
                    [],
                )
                if (
                    str(value).isdigit()
                    and int(value)
                    in valid_prompt_ids
                )
            ]

            opportunity_ids = [
                int(value)
                for value
                in action.get(
                    "impacted_opportunity_ids",
                    [],
                )
                if (
                    str(value).isdigit()
                    and int(value)
                    in valid_opportunity_ids
                )
            ]

            priority = str(
                action.get(
                    "priority",
                    "medium",
                )
            ).lower()

            if priority not in {
                "high",
                "medium",
                "low",
            }:
                priority = "medium"

            effort = str(
                action.get(
                    "effort",
                    "medium",
                )
            ).lower()

            if effort not in {
                "small",
                "medium",
                "large",
            }:
                effort = "medium"

            GeoActionPlanRepository.create_item(
                db=db,
                action_plan_id=
                    plan.id,
                sort_order=
                    index,
                priority=
                    priority,
                action_type=
                    str(
                        action.get(
                            "action_type",
                            "content",
                        )
                    )[:50],
                title=
                    str(
                        action.get(
                            "title",
                            "GEO optimization action",
                        )
                    )[:255],
                rationale=
                    str(
                        action.get(
                            "rationale",
                            "",
                        )
                    ),
                target_page=(
                    str(
                        action.get(
                            "target_page"
                        )
                    )[:500]
                    if action.get(
                        "target_page"
                    )
                    else None
                ),
                impacted_prompt_ids=
                    sorted(
                        set(prompt_ids)
                    ),
                impacted_opportunity_ids=
                    sorted(
                        set(
                            opportunity_ids
                        )
                    ),
                implementation_steps=
                    action.get(
                        "implementation_steps",
                        [],
                    ),
                evidence=
                    action.get(
                        "evidence",
                        [],
                    ),
                success_metrics=
                    action.get(
                        "success_metrics",
                        [],
                    ),
                dependencies=
                    action.get(
                        "dependencies",
                        [],
                    ),
                effort=
                    effort,
                status="open",
            )

        db.commit()
        db.refresh(plan)

        return cls.serialize(
            db,
            plan,
        )

    @staticmethod
    def serialize(
        db: Session,
        plan,
    ) -> dict:

        actions = (
            GeoActionPlanRepository.list_items(
                db,
                plan.id,
            )
        )

        return {
            "id": plan.id,
            "experiment_id":
                plan.experiment_id,
            "project_id":
                plan.project_id,
            "target_brand_id":
                plan.target_brand_id,
            "model_id":
                plan.model_id,
            "status":
                plan.status,
            "strategy_summary":
                plan.strategy_summary,
            "baseline_metrics":
                plan.baseline_metrics,
            "source_diagnosis_ids":
                plan.source_diagnosis_ids,
            "recommended_sequence":
                plan.recommended_sequence,
            "risks_and_limits":
                plan.risks_and_limits,
            "created_at":
                plan.created_at,
            "actions":
                actions,
        }

    @classmethod
    def latest(
        cls,
        db: Session,
        experiment_id: int,
    ) -> dict:

        plan = (
            GeoActionPlanRepository.latest(
                db,
                experiment_id,
            )
        )

        if plan is None:
            raise HTTPException(
                status_code=404,
                detail="No GEO action plan exists.",
            )

        return cls.serialize(
            db,
            plan,
        )
