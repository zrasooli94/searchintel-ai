from collections import defaultdict
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ai_response import AIResponse
from app.models.ai_run import AIRun
from app.models.prompt import Prompt
from app.models.site_rag_source import SiteRAGSource
from app.repositories.geo_experiment_repository import (
    GeoExperimentRepository,
)
from app.repositories.project_brand_repository import (
    ProjectBrandRepository,
)
from app.repositories.site_rag_gap_repository import (
    SiteRAGGapRepository,
)
from app.repositories.site_rag_gap_analysis_repository import (
    SiteRAGGapAnalysisRepository,
)
from app.services.site_rag_metrics_service import (
    SiteRAGMetricsService,
)


class SiteRAGGapService:

    GAP_VERSION = "site-rag-gap-v1"

    CATEGORY_WEIGHTS = {
        "commercial": 1.00,
        "comparison": 1.00,
        "recommendation": 1.00,
        "transactional": 1.00,
        "problem_solution": 0.90,
        "informational": 0.80,
        "brand": 0.80,
        "navigational": 0.60,
    }

    COMPETITIVE_TERMS = (
        "best ",
        "alternative",
        "alternatives",
        "compare ",
        "comparison",
        "versus",
        " vs ",
        "leading ",
        "top ",
    )

    PROOF_TERMS = (
        "case study",
        "case studies",
        "customer result",
        "customer results",
        "roi",
        "proof",
        "benchmark result",
        "measurable result",
    )

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

    @classmethod
    def classify_gap(
        cls,
        prompt: Prompt,
    ) -> str:
        text = (
            f" {prompt.text.lower()} "
        )

        if (
            prompt.category
            in {
                "comparison",
                "recommendation",
            }
            or any(
                term in text
                for term
                in cls.COMPETITIVE_TERMS
            )
        ):
            return "competitive_evidence_gap"

        if any(
            term in text
            for term
            in cls.PROOF_TERMS
        ):
            return "insufficient_proof_evidence"

        if (
            prompt.category
            == "problem_solution"
        ):
            return "insufficient_use_case_evidence"

        if (
            prompt.category
            in {
                "commercial",
                "transactional",
            }
        ):
            return "insufficient_product_evidence"

        return "general_first_party_evidence_gap"

    @staticmethod
    def recommendation(
        gap_type: str,
    ) -> str:
        if gap_type == "competitive_evidence_gap":
            return (
                "Create or strengthen a factual "
                "evaluation/comparison resource using "
                "verifiable selection criteria. Clearly "
                "state the target product's positioning "
                "and limitations, and do not invent "
                "competitor capabilities."
            )

        if gap_type == "insufficient_proof_evidence":
            return (
                "Add verifiable proof where available, "
                "such as documented outcomes, methodology, "
                "case studies, benchmarks, or evidence. "
                "Do not fabricate results."
            )

        if gap_type == "insufficient_use_case_evidence":
            return (
                "Create or strengthen first-party use-case "
                "content that directly explains the problem, "
                "workflow, supported capabilities, limitations, "
                "and concrete implementation evidence."
            )

        if gap_type == "insufficient_product_evidence":
            return (
                "Strengthen first-party product evidence for "
                "this commercial question with supported "
                "capabilities, intended users, limitations, "
                "integrations and decision criteria."
            )

        return (
            "Publish or strengthen first-party content that "
            "directly answers this prompt with supported facts, "
            "clear entity references and verifiable evidence."
        )

    @classmethod
    def _context(
        cls,
        db: Session,
        experiment_id: int,
    ):
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

        target_rows = [
            brand
            for brand, role
            in (
                ProjectBrandRepository
                .list_brand_roles(
                    db,
                    experiment.project_id,
                )
            )
            if role == "target"
        ]

        if not target_rows:
            raise HTTPException(
                status_code=400,
                detail="Project has no target brand.",
            )

        target = target_rows[0]

        statement = (
            select(
                AIRun.id.label("run_id"),
                AIRun.prompt_id,
                AIResponse.id.label(
                    "response_id"
                ),
                AIResponse.response_text,
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
                AIRun.status
                == "completed",
                AIRun.benchmark_mode
                == "site_rag",
                AIResponse.visibility_analyzed_at
                .is_not(None),
            )
            .order_by(
                AIRun.id,
            )
        )

        rows = list(
            db.execute(statement).all()
        )

        if not rows:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Experiment has no analyzed "
                    "Site RAG measurement runs."
                ),
            )

        return (
            experiment,
            target,
            rows,
        )

    @classmethod
    def refresh(
        cls,
        db: Session,
        experiment_id: int,
    ) -> dict:
        (
            experiment,
            target,
            rows,
        ) = cls._context(
            db,
            experiment_id,
        )

        rows_by_prompt = defaultdict(
            list
        )

        for row in rows:
            rows_by_prompt[
                row.prompt_id
            ].append(row)

        prompt_ids = set(
            rows_by_prompt.keys()
        )

        prompts = {
            prompt.id: prompt
            for prompt in db.scalars(
                select(Prompt).where(
                    Prompt.id.in_(
                        prompt_ids
                    )
                )
            ).all()
        }

        response_ids = [
            row.response_id
            for row in rows
        ]

        source_rows = list(
            db.execute(
                select(
                    SiteRAGSource.response_id,
                    SiteRAGSource.rank,
                    SiteRAGSource.url,
                )
                .where(
                    SiteRAGSource.response_id
                    .in_(response_ids)
                )
            ).all()
        )

        sources_by_response = defaultdict(
            list
        )

        for source in source_rows:
            sources_by_response[
                source.response_id
            ].append(source)

        SiteRAGGapRepository.clear_experiment(
            db,
            experiment_id,
        )

        gap_count = 0

        for prompt_id in sorted(
            prompt_ids
        ):
            prompt = prompts.get(
                prompt_id
            )

            if prompt is None:
                continue

            prompt_rows = (
                rows_by_prompt[
                    prompt_id
                ]
            )

            unsupported_rows = [
                row
                for row in prompt_rows
                if (
                    SiteRAGMetricsService
                    .is_unsupported_answer(
                        row.response_text
                    )
                )
            ]

            if not unsupported_rows:
                continue

            run_count = len(
                prompt_rows
            )

            unsupported_runs = len(
                unsupported_rows
            )

            answerable_runs = (
                run_count
                - unsupported_runs
            )

            unsupported_rate = (
                cls.percent(
                    unsupported_runs,
                    run_count,
                )
            )

            answerability_rate = (
                cls.percent(
                    answerable_runs,
                    run_count,
                )
            )

            category_weight = (
                cls.CATEGORY_WEIGHTS.get(
                    prompt.category,
                    0.80,
                )
            )

            gap_score = round(
                unsupported_rate
                * category_weight,
                2,
            )

            gap_type = cls.classify_gap(
                prompt
            )

            retrieved_source_count = 0
            referenced_pairs = set()
            supporting_urls = set()

            for row in prompt_rows:
                sources = (
                    sources_by_response[
                        row.response_id
                    ]
                )

                retrieved_source_count += (
                    len(sources)
                )

                source_by_rank = {
                    source.rank: source
                    for source in sources
                }

                references = (
                    SiteRAGMetricsService
                    .extract_source_references(
                        row.response_text
                    )
                )

                for rank in references:
                    source = (
                        source_by_rank.get(
                            rank
                        )
                    )

                    if source is None:
                        continue

                    referenced_pairs.add(
                        (
                            row.response_id,
                            rank,
                        )
                    )

                    supporting_urls.add(
                        source.url
                    )

            SiteRAGGapRepository.create(
                db=db,
                experiment_id=
                    experiment.id,
                project_id=
                    experiment.project_id,
                prompt_id=
                    prompt.id,
                target_brand_id=
                    target.id,
                prompt_text=
                    prompt.text,
                category=
                    prompt.category,
                intent=
                    prompt.intent,
                run_count=
                    run_count,
                answerable_runs=
                    answerable_runs,
                unsupported_runs=
                    unsupported_runs,
                answerability_rate=
                    answerability_rate,
                unsupported_rate=
                    unsupported_rate,
                gap_type=
                    gap_type,
                gap_score=
                    gap_score,
                priority=
                    cls.priority_from_score(
                        gap_score
                    ),
                evidence={
                    "gap_version":
                        cls.GAP_VERSION,

                    "benchmark_mode":
                        "site_rag",

                    "measurement_basis":
                        "first_party_answerability",

                    "category_weight":
                        category_weight,

                    "retrieved_source_count":
                        retrieved_source_count,

                    "referenced_source_count":
                        len(
                            referenced_pairs
                        ),

                    "supporting_urls":
                        sorted(
                            supporting_urls
                        )[:10],

                    "unsupported_run_ids": [
                        row.run_id
                        for row
                        in unsupported_rows
                    ],

                    "unsupported_response_ids": [
                        row.response_id
                        for row
                        in unsupported_rows
                    ],
                },
                recommendation=
                    cls.recommendation(
                        gap_type
                    ),
            )

            gap_count += 1

        SiteRAGGapAnalysisRepository.record_completed(
            db=db,
            experiment_id=experiment.id,
            project_id=experiment.project_id,
            target_brand_id=target.id,
            gap_version=cls.GAP_VERSION,
            total_prompts=len(prompt_ids),
            gap_count=gap_count,
            refreshed_at=datetime.now(timezone.utc),
        )

        db.commit()

        from app.services.agency_inbox_service import AgencyInboxService
        AgencyInboxService.reconcile_safely(db, experiment.project_id)
        return cls.summary(
            db,
            experiment_id,
        )

    @classmethod
    def summary(
        cls,
        db: Session,
        experiment_id: int,
    ) -> dict:
        (
            experiment,
            target,
            rows,
        ) = cls._context(
            db,
            experiment_id,
        )

        records = (
            SiteRAGGapRepository
            .list_by_experiment(
                db,
                experiment_id,
            )
        )

        analysis = SiteRAGGapAnalysisRepository.completed_by_experiment(
            db,
            experiment_id,
        )

        metrics = (
            SiteRAGMetricsService.calculate(
                db=db,
                project_id=experiment.project_id,
                experiment_id=experiment_id,
            )
        )

        total_prompts = len(
            {
                row.prompt_id
                for row in rows
            }
        )

        gap_type_counts = defaultdict(
            int
        )

        for record in records:
            gap_type_counts[
                record.gap_type
            ] += 1

        return {
            "experiment_id":
                experiment.id,

            "project_id":
                experiment.project_id,

            "target_brand_id":
                target.id,

            "target_brand":
                target.name,

            "analysis_status": (
                "completed"
                if analysis is not None
                else "pending"
            ),

            "total_prompts":
                total_prompts,

            "gap_prompts":
                len(records),

            "covered_prompts":
                total_prompts
                - len(records),

            "high_priority":
                sum(
                    item.priority == "high"
                    for item in records
                ),

            "medium_priority":
                sum(
                    item.priority == "medium"
                    for item in records
                ),

            "low_priority":
                sum(
                    item.priority == "low"
                    for item in records
                ),

            "gap_type_counts":
                dict(
                    gap_type_counts
                ),

            "site_answerability_rate_v1":
                metrics[
                    "site_answerability_rate_v1"
                ],

            "unsupported_answer_rate_v1":
                metrics[
                    "unsupported_answer_rate_v1"
                ],

            "evidence_coverage_rate":
                metrics[
                    "evidence_coverage_rate"
                ],

            "source_reference_rate":
                metrics[
                    "source_reference_rate"
                ],

            "evidence_utilization_rate":
                metrics[
                    "evidence_utilization_rate"
                ],

            "gaps":
                records,
        }
