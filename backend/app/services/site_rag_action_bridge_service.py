from collections import defaultdict

from sqlalchemy.orm import Session

from app.repositories.geo_experiment_repository import (
    GeoExperimentRepository,
)
from app.repositories.site_rag_gap_analysis_repository import (
    SiteRAGGapAnalysisRepository,
)
from app.repositories.site_rag_gap_repository import (
    SiteRAGGapRepository,
)
from app.services.site_rag_metrics_service import (
    SiteRAGMetricsService,
)


class SiteRAGActionBridgeService:

    PRIORITY_RANK = {
        "high": 3,
        "medium": 2,
        "low": 1,
    }

    ACTION_SPECS = {
        "competitive_evidence_gap": {
            "title": (
                "Create a factual comparison "
                "and evaluation resource"
            ),
            "rationale": (
                "The affected prompts require "
                "multi-option evaluation evidence "
                "that the current first-party corpus "
                "does not substantiate."
            ),
            "effort": "medium",
            "implementation_steps": [
                (
                    "Define transparent selection "
                    "criteria relevant to the "
                    "affected prompts."
                ),
                (
                    "Document the target product's "
                    "supported capabilities, intended "
                    "users, positioning, and limitations."
                ),
                (
                    "Add competitor capabilities only "
                    "when they can be verified from "
                    "reliable evidence."
                ),
                (
                    "Structure the resource so the "
                    "affected comparison and recommendation "
                    "questions can be answered directly."
                ),
            ],
            "dependencies": [
                (
                    "Verified target-product capability "
                    "and limitation documentation."
                ),
                (
                    "Verified competitor evidence before "
                    "publishing comparative claims."
                ),
            ],
        },

        "insufficient_product_evidence": {
            "title": (
                "Strengthen first-party "
                "product evidence"
            ),
            "rationale": (
                "The current first-party corpus does "
                "not provide enough supported product "
                "detail to answer the affected "
                "commercial prompts."
            ),
            "effort": "medium",
            "implementation_steps": [
                (
                    "Document supported capabilities "
                    "and intended users."
                ),
                (
                    "Add product limitations and "
                    "decision criteria."
                ),
                (
                    "Document integrations or workflows "
                    "only where verified."
                ),
                (
                    "Provide direct answers to the "
                    "affected commercial prompts."
                ),
            ],
            "dependencies": [
                "Verified product documentation.",
            ],
        },

        "insufficient_use_case_evidence": {
            "title": (
                "Expand first-party use-case evidence"
            ),
            "rationale": (
                "The website does not yet contain "
                "enough grounded evidence to answer "
                "the affected use-case questions."
            ),
            "effort": "medium",
            "implementation_steps": [
                (
                    "Describe the user problem and "
                    "operational workflow directly."
                ),
                (
                    "Document where the product "
                    "participates in the workflow."
                ),
                (
                    "Include supported limitations "
                    "and implementation requirements."
                ),
                (
                    "Connect the use case to relevant "
                    "product and technical pages."
                ),
            ],
            "dependencies": [
                "Verified workflow documentation.",
            ],
        },

        "insufficient_proof_evidence": {
            "title": (
                "Add verifiable proof evidence"
            ),
            "rationale": (
                "The affected prompts require proof "
                "that is not sufficiently documented "
                "in the current first-party corpus."
            ),
            "effort": "medium",
            "implementation_steps": [
                (
                    "Identify claims that require "
                    "supporting proof."
                ),
                (
                    "Document methodology, outcomes, "
                    "benchmarks, or case evidence "
                    "where genuinely available."
                ),
                (
                    "Avoid fabricated statistics "
                    "or unsupported customer claims."
                ),
            ],
            "dependencies": [
                "Verifiable supporting evidence.",
            ],
        },

        "general_first_party_evidence_gap": {
            "title": (
                "Strengthen direct first-party "
                "answer coverage"
            ),
            "rationale": (
                "The current website evidence is "
                "insufficient to fully ground the "
                "affected prompts."
            ),
            "effort": "medium",
            "implementation_steps": [
                (
                    "Create a direct answer for each "
                    "affected information need."
                ),
                (
                    "Support the answer with factual "
                    "first-party evidence."
                ),
                (
                    "Improve internal linking to the "
                    "most relevant supporting pages."
                ),
            ],
            "dependencies": [
                "Verified first-party information.",
            ],
        },
    }

    @classmethod
    def build(
        cls,
        db: Session,
        project_id: int,
    ) -> dict | None:

        analysis = (
            SiteRAGGapAnalysisRepository
            .latest_completed_by_project(
                db,
                project_id,
            )
        )

        if analysis is None:
            return None

        if analysis.gap_count == 0:
            return None

        experiment_id = analysis.experiment_id

        experiment = (
            GeoExperimentRepository.get(
                db,
                experiment_id,
            )
        )

        if experiment is None:
            return None

        gaps = (
            SiteRAGGapRepository
            .list_by_experiment(
                db,
                experiment_id,
            )
        )

        if not gaps:
            return None

        metrics = (
            SiteRAGMetricsService.calculate(
                db=db,
                project_id=project_id,
                experiment_id=experiment_id,
            )
        )

        grouped = defaultdict(list)

        for gap in gaps:
            grouped[
                gap.gap_type
            ].append(gap)

        actions = []

        for gap_type, group in grouped.items():
            spec = (
                cls.ACTION_SPECS.get(
                    gap_type,
                    cls.ACTION_SPECS[
                        "general_first_party_evidence_gap"
                    ],
                )
            )

            priority = max(
                group,
                key=lambda item:
                    cls.PRIORITY_RANK.get(
                        item.priority,
                        0,
                    ),
            ).priority

            gap_score = max(
                item.gap_score
                for item in group
            )

            prompt_ids = sorted({
                item.prompt_id
                for item in group
            })

            gap_ids = sorted({
                item.id
                for item in group
            })

            evidence = [
                (
                    f"{len(group)} persisted Site RAG "
                    f"prompt gap(s) share the "
                    f"{gap_type} classification."
                ),
                (
                    "Impacted prompt IDs: "
                    + ", ".join(
                        str(value)
                        for value in prompt_ids
                    )
                    + "."
                ),
            ]

            answerability = metrics.get(
                "site_answerability_rate_v1"
            )

            coverage = metrics.get(
                "evidence_coverage_rate"
            )

            utilization = metrics.get(
                "evidence_utilization_rate"
            )

            if answerability is not None:
                evidence.append(
                    "Site Answerability V1: "
                    f"{answerability}%."
                )

            if coverage is not None:
                evidence.append(
                    "Evidence coverage: "
                    f"{coverage}%."
                )

            if utilization is not None:
                evidence.append(
                    "Evidence utilization: "
                    f"{utilization}%."
                )

            success_metrics = [
                (
                    "Re-run Site RAG and reduce "
                    "unsupported answers for the "
                    "impacted prompt IDs."
                ),
                (
                    "Increase Site Answerability V1 "
                    "without weakening source-reference "
                    "integrity."
                ),
                (
                    "Preserve grounded answers based "
                    "only on supported first-party "
                    "evidence."
                ),
            ]

            actions.append(
                {
                    "gap_type":
                        gap_type,

                    "gap_count":
                        len(group),

                    "gap_score":
                        gap_score,

                    "priority":
                        priority,

                    "action_type":
                        "first_party_content",

                    "title":
                        spec["title"],

                    "rationale":
                        spec["rationale"],

                    "impacted_prompt_ids":
                        prompt_ids,

                    "impacted_gap_ids":
                        gap_ids,

                    "implementation_steps":
                        spec[
                            "implementation_steps"
                        ],

                    "evidence":
                        evidence,

                    "success_metrics":
                        success_metrics,

                    "dependencies":
                        spec["dependencies"],

                    "effort":
                        spec["effort"],
                }
            )

        actions.sort(
            key=lambda item: (
                -cls.PRIORITY_RANK.get(
                    item["priority"],
                    0,
                ),
                -item["gap_score"],
                item["gap_type"],
            )
        )

        total_prompts = metrics.get(
            "site_rag_analyzed_prompts",
            0,
        )

        return {
            "experiment_id":
                experiment.id,

            "experiment_name":
                experiment.name,

            "benchmark_mode":
                "site_rag",

            "total_prompts":
                total_prompts,

            "gap_prompts":
                len(gaps),

            "covered_prompts":
                max(
                    total_prompts - len(gaps),
                    0,
                ),

            "answerability_rate":
                metrics.get(
                    "site_answerability_rate_v1"
                ),

            "unsupported_rate":
                metrics.get(
                    "unsupported_answer_rate_v1"
                ),

            "evidence_coverage_rate":
                metrics.get(
                    "evidence_coverage_rate"
                ),

            "evidence_utilization_rate":
                metrics.get(
                    "evidence_utilization_rate"
                ),

            "actions":
                actions,

            "provenance_note": (
                "These actions are derived "
                "deterministically from the latest "
                "persisted Site RAG gap records. "
                "They do not rewrite the historical "
                "GEO action plan and do not trigger "
                "new AI or web-search runs."
            ),
        }
