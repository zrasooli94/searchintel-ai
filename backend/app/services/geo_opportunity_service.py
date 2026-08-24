from collections import defaultdict

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ai_response import AIResponse
from app.models.ai_run import AIRun
from app.models.brand_mention import BrandMention
from app.models.prompt import Prompt
from app.models.web_search_source import (
    WebSearchSource,
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


class GeoOpportunityService:

    CATEGORY_WEIGHTS = {
        "brand": 1.00,
        "commercial": 1.00,
        "comparison": 1.00,
        "recommendation": 1.00,
        "transactional": 1.00,
        "navigational": 0.95,
        "problem_solution": 0.90,
        "informational": 0.80,
    }

    @staticmethod
    def percent(
        numerator: int | float,
        denominator: int | float,
    ) -> float:
        if not denominator:
            return 0.0

        return round(
            numerator / denominator * 100,
            2,
        )

    @staticmethod
    def priority_from_score(
        score: float,
    ) -> str:
        if score >= 75:
            return "high"

        if score >= 50:
            return "medium"

        return "low"

    @staticmethod
    def gap_type(
        target_rate: float,
        competitor_pressure: float,
    ) -> str:

        if (
            target_rate == 0
            and competitor_pressure >= 50
        ):
            return "competitor_dominance"

        if target_rate == 0:
            return "target_absent"

        if target_rate < 50:
            return "weak_visibility"

        if target_rate < 100:
            return "inconsistent_visibility"

        return "covered"

    @staticmethod
    def recommendation(
        category: str,
        gap_type: str,
        top_competitor: str | None,
    ) -> str:

        competitor = (
            top_competitor
            if top_competitor
            else "competing brands"
        )

        if gap_type == "covered":
            return (
                "Maintain this topic and monitor whether "
                "the target continues appearing across "
                "future benchmark runs."
            )

        if category == "brand":
            return (
                "Strengthen the canonical brand/entity "
                "page with a clear description, products, "
                "use cases, evidence, organization details, "
                "and consistent brand references across "
                "the website and trusted external sources."
            )

        if category in {
            "commercial",
            "comparison",
            "recommendation",
            "transactional",
        }:
            return (
                "Create or strengthen content that directly "
                "answers this commercial prompt. Explain "
                "who the solution is for, key capabilities, "
                "differentiators, proof points, integrations, "
                "and comparison criteria. Review why "
                f"{competitor} is currently winning this "
                "prompt."
            )

        if category == "problem_solution":
            return (
                "Publish an authoritative problem-solution "
                "resource with operational guidance, concrete "
                "examples, measurable outcomes, and evidence "
                "showing how the target addresses this need. "
                f"Compare the evidence with {competitor}."
            )

        return (
            "Strengthen topical authority for this question "
            "with a direct answer, supporting evidence, "
            "clear entity references, internal linking, "
            "structured information, and original expertise. "
            f"Review the coverage provided by {competitor}."
        )

    @classmethod
    def refresh(
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
            raise HTTPException(
                status_code=404,
                detail="Experiment not found.",
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
                detail="Project has no target brand.",
            )

        target = target_rows[0]

        competitor_map = {
            brand.id: brand.name
            for brand, role
            in project_brands
            if role == "competitor"
        }

        run_statement = (
            select(
                AIRun.id.label("run_id"),
                AIRun.prompt_id,
                AIRun.benchmark_mode,
                AIResponse.id.label(
                    "response_id"
                ),
            )
            .join(
                AIResponse,
                AIResponse.run_id
                == AIRun.id,
            )
            .where(
                AIRun.experiment_id
                == experiment_id,
                AIRun.include_in_metrics
                .is_(True),
                AIRun.status == "completed",
                AIResponse.visibility_analyzed_at
                .is_not(None),
            )
        )

        run_rows = list(
            db.execute(
                run_statement
            ).all()
        )

        if not run_rows:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Experiment has no analyzed "
                    "measurement runs."
                ),
            )

        benchmark_modes = {
            (
                row.benchmark_mode
                or "memory"
            )
            for row in run_rows
        }

        if len(benchmark_modes) > 1:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Prompt opportunity analysis "
                    "does not support mixed benchmark "
                    "modes in one experiment."
                ),
            )

        benchmark_mode = next(
            iter(benchmark_modes)
        )

        measurement_basis = (
            "grounded_response_presence"
            if benchmark_mode == "web_search"
            else "resolved_textual_mention"
        )

        response_to_prompt = {
            row.response_id: row.prompt_id
            for row in run_rows
        }

        prompt_response_ids = defaultdict(
            list
        )

        for row in run_rows:
            prompt_response_ids[
                row.prompt_id
            ].append(
                row.response_id
            )

        prompt_ids = set(
            prompt_response_ids.keys()
        )

        prompt_statement = (
            select(Prompt)
            .where(
                Prompt.id.in_(
                    prompt_ids
                )
            )
        )

        prompts = {
            prompt.id: prompt
            for prompt in db.scalars(
                prompt_statement
            ).all()
        }

        response_ids = list(
            response_to_prompt.keys()
        )

        mention_statement = (
            select(BrandMention)
            .where(
                BrandMention.response_id.in_(
                    response_ids
                ),
                BrandMention.resolution_status
                == "resolved",
                BrandMention.brand_id
                .is_not(None),
            )
        )

        mentions = list(
            db.scalars(
                mention_statement
            ).all()
        )

        grounded_brand_response_pairs: set[
            tuple[int, int]
        ] = set()

        if benchmark_mode == "web_search":

            source_statement = (
                select(
                    WebSearchSource.response_id,
                    WebSearchSource.brand_id,
                )
                .where(
                    WebSearchSource.response_id.in_(
                        response_ids
                    ),
                    WebSearchSource.brand_id
                    .is_not(None),
                )
            )

            grounded_brand_response_pairs = {
                (
                    response_id,
                    brand_id,
                )
                for (
                    response_id,
                    brand_id,
                )
                in db.execute(
                    source_statement
                ).all()
                if brand_id is not None
            }

        target_response_sets = defaultdict(
            set
        )

        competitor_stats = defaultdict(
            lambda: defaultdict(
                lambda: {
                    "responses": set(),
                    "mention_count": 0,
                    "positions": [],
                }
            )
        )

        for mention in mentions:
            prompt_id = response_to_prompt.get(
                mention.response_id
            )

            if prompt_id is None:
                continue

            if (
                benchmark_mode == "web_search"
                and (
                    mention.response_id,
                    mention.brand_id,
                )
                not in grounded_brand_response_pairs
            ):
                continue

            if mention.brand_id == target.id:
                target_response_sets[
                    prompt_id
                ].add(
                    mention.response_id
                )

                continue

            if mention.brand_id not in competitor_map:
                continue

            stats = competitor_stats[
                prompt_id
            ][mention.brand_id]

            stats["responses"].add(
                mention.response_id
            )

            stats["mention_count"] += (
                mention.mention_count
            )

            stats["positions"].append(
                mention.position
            )

        GeoOpportunityRepository.clear_experiment(
            db,
            experiment_id,
        )

        for prompt_id in sorted(
            prompt_ids
        ):
            prompt = prompts.get(
                prompt_id
            )

            if prompt is None:
                continue

            response_ids_for_prompt = (
                prompt_response_ids[
                    prompt_id
                ]
            )

            run_count = len(
                response_ids_for_prompt
            )

            target_mention_runs = len(
                target_response_sets[
                    prompt_id
                ]
            )

            target_rate = cls.percent(
                target_mention_runs,
                run_count,
            )

            competitor_evidence = []

            for (
                brand_id,
                stats,
            ) in competitor_stats[
                prompt_id
            ].items():

                run_coverage = cls.percent(
                    len(
                        stats["responses"]
                    ),
                    run_count,
                )

                positions = stats[
                    "positions"
                ]

                average_position = round(
                    sum(positions)
                    / len(positions),
                    2,
                )

                competitor_evidence.append(
                    {
                        "brand_id": brand_id,
                        "name":
                            competitor_map[
                                brand_id
                            ],
                        "run_coverage":
                            run_coverage,
                        "mention_count":
                            stats[
                                "mention_count"
                            ],
                        "average_position":
                            average_position,
                    }
                )

            competitor_evidence.sort(
                key=lambda item: (
                    -item[
                        "run_coverage"
                    ],
                    -item[
                        "mention_count"
                    ],
                    item[
                        "average_position"
                    ],
                )
            )

            top = (
                competitor_evidence[0]
                if competitor_evidence
                else None
            )

            competitor_pressure = (
                top["run_coverage"]
                if top
                else 0.0
            )

            visibility_gap = (
                100.0 - target_rate
            )

            category_weight = (
                cls.CATEGORY_WEIGHTS.get(
                    prompt.category,
                    0.80,
                )
            )

            opportunity_score = round(
                (
                    visibility_gap * 0.70
                    + competitor_pressure * 0.30
                )
                * category_weight,
                2,
            )

            gap_type = cls.gap_type(
                target_rate,
                competitor_pressure,
            )

            priority = (
                cls.priority_from_score(
                    opportunity_score
                )
            )

            recommendation = (
                cls.recommendation(
                    prompt.category,
                    gap_type,
                    (
                        top["name"]
                        if top
                        else None
                    ),
                )
            )

            GeoOpportunityRepository.create(
                db=db,
                experiment_id=experiment.id,
                project_id=experiment.project_id,
                prompt_id=prompt.id,
                target_brand_id=target.id,
                prompt_text=prompt.text,
                category=prompt.category,
                intent=prompt.intent,
                run_count=run_count,
                target_mention_runs=
                    target_mention_runs,
                target_mention_rate=
                    target_rate,
                top_competitor_brand_id=(
                    top["brand_id"]
                    if top
                    else None
                ),
                top_competitor_name=(
                    top["name"]
                    if top
                    else None
                ),
                top_competitor_run_coverage=
                    competitor_pressure,
                opportunity_score=
                    opportunity_score,
                priority=priority,
                gap_type=gap_type,
                evidence={
                    "competitors":
                        competitor_evidence[
                            :5
                        ],
                    "visibility_gap":
                        visibility_gap,
                    "category_weight":
                        category_weight,

                    "benchmark_mode":
                        benchmark_mode,

                    "measurement_basis":
                        measurement_basis,

                    "web_grounding_note": (
                        (
                            "Web-search opportunity "
                            "presence requires both a "
                            "resolved textual brand "
                            "mention and same-brand "
                            "first-party source retrieval "
                            "within the response. "
                            "Competitor pressure depends "
                            "on registered domain "
                            "coverage."
                        )
                        if benchmark_mode
                        == "web_search"
                        else None
                    ),
                },
                recommendation=
                    recommendation,
            )

        db.commit()

        return cls.summary(
            db,
            experiment_id,
        )

    @staticmethod
    def summary(
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
                detail="Project has no target brand.",
            )

        target = target_rows[0]

        opportunities = (
            GeoOpportunityRepository
            .list_by_experiment(
                db,
                experiment_id,
            )
        )

        return {
            "experiment_id":
                experiment_id,
            "project_id":
                experiment.project_id,
            "target_brand_id":
                target.id,
            "target_brand":
                target.name,
            "total_prompts":
                len(opportunities),
            "high_priority":
                sum(
                    item.priority == "high"
                    for item in opportunities
                ),
            "medium_priority":
                sum(
                    item.priority == "medium"
                    for item in opportunities
                ),
            "low_priority":
                sum(
                    item.priority == "low"
                    for item in opportunities
                ),
            "target_absent_prompts":
                sum(
                    item.gap_type
                    == "target_absent"
                    for item in opportunities
                ),
            "competitor_dominance_prompts":
                sum(
                    item.gap_type
                    == "competitor_dominance"
                    for item in opportunities
                ),
            "covered_prompts":
                sum(
                    item.gap_type
                    == "covered"
                    for item in opportunities
                ),
            "opportunities":
                opportunities,
        }
