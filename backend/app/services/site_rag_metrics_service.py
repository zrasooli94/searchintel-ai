import re
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ai_response import AIResponse
from app.models.ai_run import AIRun
from app.models.site_rag_source import (
    SiteRAGSource,
)


class SiteRAGMetricsService:

    SOURCE_REFERENCE_GROUP_PATTERN = re.compile(
        r"\[\s*Sources?\s*([^\]]+)\]",
        re.IGNORECASE,
    )

    SOURCE_REFERENCE_NUMBER_PATTERN = re.compile(
        r"\d+"
    )

    UNSUPPORTED_PATTERNS = (
        re.compile(
            r"\binsufficient evidence\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\bevidence is insufficient\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\bprovided evidence\b.{0,160}"
            r"\binsufficient\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\bnot enough "
            r"(?:first-party )?evidence\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\bcannot "
            r"(?:answer|determine|establish)\b"
            r".{0,160}\bprovided evidence\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\bunable to "
            r"(?:answer|determine)\b"
            r".{0,160}\bprovided evidence\b",
            re.IGNORECASE,
        ),
    )

    @staticmethod
    def percent(
        numerator: int | float,
        denominator: int | float,
    ) -> float:
        if denominator == 0:
            return 0.0

        return round(
            numerator
            / denominator
            * 100,
            2,
        )

    @classmethod
    def extract_source_references(
        cls,
        response_text: str,
    ) -> set[int]:
        references: set[int] = set()

        groups = (
            cls.SOURCE_REFERENCE_GROUP_PATTERN
            .findall(
                response_text or ""
            )
        )

        for group in groups:
            references.update(
                int(value)
                for value
                in (
                    cls.SOURCE_REFERENCE_NUMBER_PATTERN
                    .findall(group)
                )
            )

        return references

    @classmethod
    def is_unsupported_answer(
        cls,
        response_text: str,
    ) -> bool:
        normalized = re.sub(
            r"\s+",
            " ",
            response_text or "",
        ).strip()

        return any(
            pattern.search(normalized)
            is not None
            for pattern
            in cls.UNSUPPORTED_PATTERNS
        )

    @staticmethod
    def empty() -> dict:
        return {
            "site_rag_analyzed_runs": 0,
            "site_rag_analyzed_prompts": 0,

            "evidence_coverage_rate": None,
            "source_reference_rate": None,
            "evidence_utilization_rate": None,

            "site_answerability_rate_v1": None,
            "unsupported_answer_rate_v1": None,

            "unique_supporting_pages": 0,
            "unique_supporting_urls": 0,

            "avg_sources_per_response": None,

            "top_supporting_pages": [],
        }

    @classmethod
    def calculate(
        cls,
        db: Session,
        project_id: int,
        experiment_id: int | None = None,
    ) -> dict:
        statement = (
            select(
                AIResponse.id,
                AIResponse.response_text,
                AIRun.prompt_id,
            )
            .join(
                AIRun,
                AIResponse.run_id
                == AIRun.id,
            )
            .where(
                AIRun.project_id
                == project_id,
                AIRun.include_in_metrics
                .is_(True),
                AIRun.benchmark_mode
                == "site_rag",
                AIResponse.visibility_analyzed_at
                .is_not(None),
            )
        )

        if experiment_id is not None:
            statement = statement.where(
                AIRun.experiment_id
                == experiment_id
            )

        responses = list(
            db.execute(statement).all()
        )

        if not responses:
            return cls.empty()

        response_ids = [
            row.id
            for row in responses
        ]

        sources = list(
            db.scalars(
                select(
                    SiteRAGSource
                ).where(
                    SiteRAGSource.response_id
                    .in_(response_ids)
                )
            ).all()
        )

        sources_by_response: dict[
            int,
            list[SiteRAGSource],
        ] = defaultdict(list)

        for source in sources:
            sources_by_response[
                source.response_id
            ].append(source)

        responses_with_evidence = 0
        responses_with_references = 0
        unsupported_responses = 0

        total_retrieved_sources = len(
            sources
        )

        utilized_source_keys: set[
            tuple[int, int]
        ] = set()

        page_stats: dict[
            tuple[int | None, str, str | None],
            dict,
        ] = {}

        for row in responses:
            response_sources = (
                sources_by_response.get(
                    row.id,
                    [],
                )
            )

            if response_sources:
                responses_with_evidence += 1

            source_by_rank = {
                source.rank: source
                for source
                in response_sources
            }

            referenced_ranks = (
                cls.extract_source_references(
                    row.response_text
                )
            )

            valid_ranks = {
                rank
                for rank
                in referenced_ranks
                if rank in source_by_rank
            }

            if valid_ranks:
                responses_with_references += 1

            if cls.is_unsupported_answer(
                row.response_text
            ):
                unsupported_responses += 1

            referenced_pages_in_response: set[
                tuple[
                    int | None,
                    str,
                    str | None,
                ]
            ] = set()

            for rank in valid_ranks:
                source = source_by_rank[
                    rank
                ]

                utilized_source_keys.add(
                    (
                        row.id,
                        rank,
                    )
                )

                page_key = (
                    source.page_id,
                    source.url,
                    source.title,
                )

                if page_key not in page_stats:
                    page_stats[
                        page_key
                    ] = {
                        "page_id":
                            source.page_id,

                        "url":
                            source.url,

                        "title":
                            source.title,

                        "response_count":
                            0,

                        "reference_count":
                            0,
                    }

                page_stats[
                    page_key
                ][
                    "reference_count"
                ] += 1

                referenced_pages_in_response.add(
                    page_key
                )

            for page_key in (
                referenced_pages_in_response
            ):
                page_stats[
                    page_key
                ][
                    "response_count"
                ] += 1

        analyzed_runs = len(
            responses
        )

        analyzed_prompts = len(
            {
                row.prompt_id
                for row in responses
            }
        )

        answerable_responses = (
            analyzed_runs
            - unsupported_responses
        )

        top_supporting_pages = sorted(
            page_stats.values(),
            key=lambda item: (
                -item["reference_count"],
                -item["response_count"],
                item["url"],
            ),
        )[:10]

        return {
            "site_rag_analyzed_runs":
                analyzed_runs,

            "site_rag_analyzed_prompts":
                analyzed_prompts,

            "evidence_coverage_rate":
                cls.percent(
                    responses_with_evidence,
                    analyzed_runs,
                ),

            "source_reference_rate":
                cls.percent(
                    responses_with_references,
                    analyzed_runs,
                ),

            "evidence_utilization_rate":
                cls.percent(
                    len(
                        utilized_source_keys
                    ),
                    total_retrieved_sources,
                ),

            "site_answerability_rate_v1":
                cls.percent(
                    answerable_responses,
                    analyzed_runs,
                ),

            "unsupported_answer_rate_v1":
                cls.percent(
                    unsupported_responses,
                    analyzed_runs,
                ),

            "unique_supporting_pages":
                len(
                    {
                        item["page_id"]
                        for item
                        in page_stats.values()
                        if item["page_id"]
                        is not None
                    }
                ),

            "unique_supporting_urls":
                len(
                    {
                        item["url"]
                        for item
                        in page_stats.values()
                    }
                ),

            "avg_sources_per_response":
                round(
                    total_retrieved_sources
                    / analyzed_runs,
                    2,
                ),

            "top_supporting_pages":
                top_supporting_pages,
        }
