from collections import defaultdict

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ai_response import AIResponse
from app.models.ai_run import AIRun
from app.models.brand import Brand
from app.models.brand_mention import BrandMention
from app.models.citation import Citation
from app.models.web_search_source import WebSearchSource
from app.repositories.geo_experiment_repository import (
    GeoExperimentRepository,
)
from app.repositories.metric_snapshot_repository import (
    MetricSnapshotRepository,
)
from app.repositories.project_brand_repository import (
    ProjectBrandRepository,
)
from app.repositories.project_repository import (
    ProjectRepository,
)
from app.services.visibility_analysis_service import (
    VisibilityAnalysisService,
)


class VisibilityMetricsService:

    @staticmethod
    def percent(
        numerator: int | float,
        denominator: int | float,
    ) -> float:
        if denominator == 0:
            return 0.0

        return round(
            numerator / denominator * 100,
            2,
        )

    @classmethod
    def calculate(
        cls,
        db: Session,
        project_id: int,
        experiment_id: int | None = None,
        persist_snapshot: bool = True,
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

        if experiment_id is not None:
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

            if experiment.project_id != project_id:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Experiment does not belong "
                        "to this project."
                    ),
                )

        project_brands = (
            ProjectBrandRepository.list_brand_roles(
                db,
                project_id,
            )
        )

        target_rows = [
            (brand, role)
            for brand, role in project_brands
            if role == "target"
        ]

        if not target_rows:
            raise HTTPException(
                status_code=400,
                detail="Project has no target brand.",
            )

        target_brand = target_rows[0][0]

        # -------------------------------------------------
        # Measurement population
        # -------------------------------------------------

        response_statement = (
            select(
                AIResponse.id,
                AIRun.prompt_id,
                AIRun.benchmark_mode,
            )
            .join(
                AIRun,
                AIResponse.run_id == AIRun.id,
            )
            .where(
                AIRun.project_id == project_id,
                AIRun.include_in_metrics.is_(True),
                AIResponse.visibility_analyzed_at
                .is_not(None),
            )
        )

        if experiment_id is not None:
            response_statement = (
                response_statement.where(
                    AIRun.experiment_id
                    == experiment_id
                )
            )

        analyzed_rows = list(
            db.execute(
                response_statement
            ).all()
        )

        if not analyzed_rows:
            raise HTTPException(
                status_code=400,
                detail=(
                    "No analyzed AI responses exist. "
                    "Analyze visibility first."
                ),
            )

        response_ids = [
            row.id
            for row in analyzed_rows
        ]

        response_to_prompt = {
            row.id: row.prompt_id
            for row in analyzed_rows
        }

        analyzed_runs = len(response_ids)

        analyzed_prompt_ids = set(
            response_to_prompt.values()
        )

        benchmark_modes = sorted(
            {
                row.benchmark_mode or "memory"
                for row in analyzed_rows
            }
        )

        benchmark_mode = (
            benchmark_modes[0]
            if len(benchmark_modes) == 1
            else "mixed"
        )

        # -------------------------------------------------
        # Target mention metrics
        # -------------------------------------------------

        target_mentions = list(
            db.scalars(
                select(BrandMention).where(
                    BrandMention.response_id.in_(
                        response_ids
                    ),
                    BrandMention.brand_id
                    == target_brand.id,
                )
            ).all()
        )

        target_response_ids = {
            mention.response_id
            for mention in target_mentions
        }

        target_prompt_ids = {
            response_to_prompt[
                response_id
            ]
            for response_id
            in target_response_ids
        }

        target_mention_count = sum(
            mention.mention_count
            for mention in target_mentions
        )

        mention_rate = cls.percent(
            len(target_response_ids),
            analyzed_runs,
        )

        prompt_coverage = cls.percent(
            len(target_prompt_ids),
            len(analyzed_prompt_ids),
        )

        # -------------------------------------------------
        # Citation metrics
        # -------------------------------------------------

        all_citations = list(
            db.scalars(
                select(Citation).where(
                    Citation.response_id.in_(
                        response_ids
                    )
                )
            ).all()
        )

        target_citations = [
            citation
            for citation in all_citations
            if citation.brand_id
            == target_brand.id
        ]

        cited_response_ids = {
            citation.response_id
            for citation in target_citations
        }

        citation_rate = cls.percent(
            len(cited_response_ids),
            analyzed_runs,
        )

        # -------------------------------------------------
        # Mention position
        # -------------------------------------------------

        average_position = None

        if target_mentions:
            average_position = round(
                sum(
                    mention.position
                    for mention in target_mentions
                )
                / len(target_mentions),
                2,
            )

        position_quality = 0.0

        if average_position:
            position_quality = round(
                min(
                    100.0,
                    100.0 / average_position,
                ),
                2,
            )

        # -------------------------------------------------
        # Mention Share of Voice V1
        # -------------------------------------------------

        all_mentions = list(
            db.execute(
                select(
                    BrandMention,
                    Brand.name,
                )
                .outerjoin(
                    Brand,
                    BrandMention.brand_id
                    == Brand.id,
                )
                .where(
                    BrandMention.response_id.in_(
                        response_ids
                    ),
                    BrandMention.resolution_status
                    == "resolved",
                    BrandMention.brand_id
                    .is_not(None),
                )
            ).all()
        )

        grouped = defaultdict(
            lambda: {
                "brand_id": None,
                "name": "",
                "mention_count": 0,
            }
        )

        for mention, brand_name in all_mentions:
            key = f"brand:{mention.brand_id}"

            grouped[key]["brand_id"] = (
                mention.brand_id
            )

            grouped[key]["name"] = (
                brand_name
                or mention.mention_text
            )

            grouped[key]["mention_count"] += (
                mention.mention_count
            )

        total_mentions = sum(
            item["mention_count"]
            for item in grouped.values()
        )

        share_of_voice = []

        for item in grouped.values():
            sov = cls.percent(
                item["mention_count"],
                total_mentions,
            )

            share_of_voice.append(
                {
                    "brand_id":
                        item["brand_id"],
                    "name":
                        item["name"],
                    "mention_count":
                        item["mention_count"],
                    "share_of_voice":
                        sov,
                }
            )

        share_of_voice.sort(
            key=lambda item:
                -item["share_of_voice"]
        )

        target_sov = 0.0

        for item in share_of_voice:
            if (
                item["brand_id"]
                == target_brand.id
            ):
                target_sov = item[
                    "share_of_voice"
                ]
                break

        # -------------------------------------------------
        # Brand response-exposure metrics
        #
        # A brand counts at most once per AI response,
        # even when the response mentions both the parent
        # brand and one or more products that roll up to it.
        # -------------------------------------------------

        brand_response_sets: dict[
            int,
            set[int],
        ] = defaultdict(set)

        brand_names: dict[
            int,
            str,
        ] = {}

        for mention, brand_name in all_mentions:

            if mention.brand_id is None:
                continue

            brand_response_sets[
                mention.brand_id
            ].add(
                mention.response_id
            )

            if mention.brand_id not in brand_names:
                brand_names[
                    mention.brand_id
                ] = (
                    brand_name
                    or mention.mention_text
                )

        total_brand_response_exposures = sum(
            len(response_set)
            for response_set
            in brand_response_sets.values()
        )

        response_share_of_voice = []

        for (
            brand_id,
            response_set,
        ) in brand_response_sets.items():

            response_exposures = len(
                response_set
            )

            response_sov = cls.percent(
                response_exposures,
                total_brand_response_exposures,
            )

            response_coverage = cls.percent(
                response_exposures,
                analyzed_runs,
            )

            response_share_of_voice.append(
                {
                    "brand_id":
                        brand_id,
                    "name":
                        brand_names.get(
                            brand_id,
                            "",
                        ),
                    "response_exposures":
                        response_exposures,
                    "response_share_of_voice":
                        response_sov,
                    "response_coverage":
                        response_coverage,
                }
            )

        response_share_of_voice.sort(
            key=lambda item: (
                -item[
                    "response_exposures"
                ],
                item["name"].lower(),
            )
        )

        target_response_ids_resolved = (
            brand_response_sets.get(
                target_brand.id,
                set(),
            )
        )

        target_response_coverage = (
            cls.percent(
                len(
                    target_response_ids_resolved
                ),
                analyzed_runs,
            )
        )

        target_response_share_of_voice = (
            cls.percent(
                len(
                    target_response_ids_resolved
                ),
                total_brand_response_exposures,
            )
            if total_brand_response_exposures
            else 0.0
        )

        # -------------------------------------------------
        # Existing V1 score
        # -------------------------------------------------

        visibility_score = round(
            (
                mention_rate * 0.50
                + citation_rate * 0.20
                + prompt_coverage * 0.20
                + position_quality * 0.10
            ),
            2,
        )

        # -------------------------------------------------
        # Web-search measurement population
        # -------------------------------------------------

        web_rows = [
            row
            for row in analyzed_rows
            if row.benchmark_mode
            == "web_search"
        ]

        web_response_ids = {
            row.id
            for row in web_rows
        }

        web_search_analyzed_runs = len(
            web_response_ids
        )

        web_response_to_prompt = {
            row.id: row.prompt_id
            for row in web_rows
        }

        web_prompt_ids = set(
            web_response_to_prompt.values()
        )

        web_sources: list[
            WebSearchSource
        ] = []

        if web_response_ids:
            web_sources = list(
                db.scalars(
                    select(
                        WebSearchSource
                    ).where(
                        WebSearchSource
                        .response_id.in_(
                            web_response_ids
                        )
                    )
                ).all()
            )

        # -------------------------------------------------
        # Web-search-only metrics
        # -------------------------------------------------

        target_source_presence_rate = None
        target_source_prompt_coverage = None

        grounded_target_mention_rate = None
        grounded_target_prompt_coverage = None

        target_grounded_response_share_of_voice = None
        grounded_response_share_of_voice = []

        source_to_citation_conversion = None
        target_source_to_citation_conversion = None

        target_source_share_of_voice = None
        target_citation_share_of_voice = None

        resolved_first_party_source_rate = None

        unique_search_source_urls = 0
        unique_search_domains = 0

        web_visibility_score_v1 = None

        if web_search_analyzed_runs:

            target_source_response_ids = {
                source.response_id
                for source in web_sources
                if source.brand_id
                == target_brand.id
            }

            target_source_prompt_ids = {
                web_response_to_prompt[
                    response_id
                ]
                for response_id
                in target_source_response_ids
            }

            target_source_presence_rate = (
                cls.percent(
                    len(
                        target_source_response_ids
                    ),
                    web_search_analyzed_runs,
                )
            )

            target_source_prompt_coverage = (
                cls.percent(
                    len(
                        target_source_prompt_ids
                    ),
                    len(web_prompt_ids),
                )
            )

            web_target_mention_response_ids = {
                response_id
                for response_id
                in target_response_ids
                if response_id
                in web_response_ids
            }

            grounded_response_ids = (
                web_target_mention_response_ids
                & target_source_response_ids
            )

            grounded_prompt_ids = {
                web_response_to_prompt[
                    response_id
                ]
                for response_id
                in grounded_response_ids
            }

            grounded_target_mention_rate = (
                cls.percent(
                    len(
                        grounded_response_ids
                    ),
                    web_search_analyzed_runs,
                )
            )

            grounded_target_prompt_coverage = (
                cls.percent(
                    len(
                        grounded_prompt_ids
                    ),
                    len(web_prompt_ids),
                )
            )

            # ---------------------------------------------
            # Web-grounded brand response exposure
            #
            # A brand counts once per response only when:
            # 1. it has a resolved textual mention, and
            # 2. a source belonging to that same brand was
            #    retrieved in that same response.
            # ---------------------------------------------

            web_mention_exposures: set[
                tuple[int, int]
            ] = {
                (
                    mention.response_id,
                    mention.brand_id,
                )
                for mention, _brand_name
                in all_mentions
                if (
                    mention.response_id
                    in web_response_ids
                    and mention.brand_id
                    is not None
                )
            }

            web_source_exposures: set[
                tuple[int, int]
            ] = {
                (
                    source.response_id,
                    source.brand_id,
                )
                for source in web_sources
                if source.brand_id is not None
            }

            grounded_brand_exposures = (
                web_mention_exposures
                & web_source_exposures
            )

            grounded_brand_response_sets: dict[
                int,
                set[int],
            ] = defaultdict(set)

            for (
                response_id,
                brand_id,
            ) in grounded_brand_exposures:

                grounded_brand_response_sets[
                    brand_id
                ].add(
                    response_id
                )

            total_grounded_brand_exposures = sum(
                len(response_set)
                for response_set
                in grounded_brand_response_sets.values()
            )

            grounded_response_share_of_voice = []

            for (
                brand_id,
                response_set,
            ) in grounded_brand_response_sets.items():

                exposure_count = len(
                    response_set
                )

                grounded_response_share_of_voice.append(
                    {
                        "brand_id":
                            brand_id,
                        "name":
                            brand_names.get(
                                brand_id,
                                "",
                            ),
                        "grounded_response_exposures":
                            exposure_count,
                        "grounded_response_share_of_voice":
                            cls.percent(
                                exposure_count,
                                total_grounded_brand_exposures,
                            ),
                        "grounded_response_coverage":
                            cls.percent(
                                exposure_count,
                                web_search_analyzed_runs,
                            ),
                    }
                )

            grounded_response_share_of_voice.sort(
                key=lambda item: (
                    -item[
                        "grounded_response_exposures"
                    ],
                    item["name"].lower(),
                )
            )

            target_grounded_exposure_count = len(
                grounded_brand_response_sets.get(
                    target_brand.id,
                    set(),
                )
            )

            if total_grounded_brand_exposures:
                target_grounded_response_share_of_voice = (
                    cls.percent(
                        target_grounded_exposure_count,
                        total_grounded_brand_exposures,
                    )
                )
            else:
                target_grounded_response_share_of_voice = (
                    0.0
                )

            # A source can appear in several search
            # calls. Conversion and SOV use unique,
            # normalized URLs rather than raw rows.
            unique_source_urls: set[str] = set()
            unique_domains: set[str] = set()

            cited_source_urls: set[str] = set()

            target_source_urls: set[str] = set()
            target_cited_source_urls: set[str] = set()

            resolved_source_urls: set[str] = set()
            resolved_source_pairs: set[
                tuple[str, int]
            ] = set()

            for source in web_sources:
                normalized_url = (
                    VisibilityAnalysisService
                    .normalize_url_for_match(
                        source.url
                    )
                )

                if not normalized_url:
                    continue

                unique_source_urls.add(
                    normalized_url
                )

                if source.domain:
                    unique_domains.add(
                        source.domain.lower()
                    )

                if source.is_cited:
                    cited_source_urls.add(
                        normalized_url
                    )

                if source.brand_id is not None:
                    resolved_source_urls.add(
                        normalized_url
                    )

                    resolved_source_pairs.add(
                        (
                            normalized_url,
                            source.brand_id,
                        )
                    )

                if (
                    source.brand_id
                    == target_brand.id
                ):
                    target_source_urls.add(
                        normalized_url
                    )

                    if source.is_cited:
                        target_cited_source_urls.add(
                            normalized_url
                        )

            unique_search_source_urls = len(
                unique_source_urls
            )

            unique_search_domains = len(
                unique_domains
            )

            if unique_source_urls:
                source_to_citation_conversion = (
                    cls.percent(
                        len(cited_source_urls),
                        len(unique_source_urls),
                    )
                )

            if target_source_urls:
                target_source_to_citation_conversion = (
                    cls.percent(
                        len(
                            target_cited_source_urls
                        ),
                        len(target_source_urls),
                    )
                )

            target_source_pair_count = sum(
                1
                for _, brand_id
                in resolved_source_pairs
                if brand_id
                == target_brand.id
            )

            if resolved_source_pairs:
                target_source_share_of_voice = (
                    cls.percent(
                        target_source_pair_count,
                        len(
                            resolved_source_pairs
                        ),
                    )
                )

            if unique_source_urls:
                resolved_first_party_source_rate = (
                    cls.percent(
                        len(resolved_source_urls),
                        len(unique_source_urls),
                    )
                )

            # Citation SOV is also restricted to
            # web-search responses and unique URLs.
            resolved_citation_pairs: set[
                tuple[str, int]
            ] = set()

            for citation in all_citations:

                if (
                    citation.response_id
                    not in web_response_ids
                    or citation.brand_id
                    is None
                ):
                    continue

                normalized_url = (
                    VisibilityAnalysisService
                    .normalize_url_for_match(
                        citation.url
                    )
                )

                if not normalized_url:
                    continue

                resolved_citation_pairs.add(
                    (
                        normalized_url,
                        citation.brand_id,
                    )
                )

            target_citation_pair_count = sum(
                1
                for _, brand_id
                in resolved_citation_pairs
                if brand_id
                == target_brand.id
            )

            if resolved_citation_pairs:
                target_citation_share_of_voice = (
                    cls.percent(
                        target_citation_pair_count,
                        len(
                            resolved_citation_pairs
                        ),
                    )
                )

            web_visibility_score_v1 = round(
                (
                    (
                        grounded_target_mention_rate
                        or 0.0
                    ) * 0.30
                    + (
                        target_source_presence_rate
                        or 0.0
                    ) * 0.25
                    + citation_rate * 0.20
                    + (
                        grounded_target_prompt_coverage
                        or 0.0
                    ) * 0.15
                    + (
                        target_source_share_of_voice
                        or 0.0
                    ) * 0.10
                ),
                2,
            )

        # -------------------------------------------------
        # Metric persistence
        # -------------------------------------------------

        metrics = {
            "mention_rate":
                mention_rate,
            "prompt_coverage":
                prompt_coverage,
            "citation_rate":
                citation_rate,
            "target_share_of_voice":
                target_sov,
            "target_response_share_of_voice":
                target_response_share_of_voice,
            "target_response_coverage":
                target_response_coverage,
            "visibility_score_v1":
                visibility_score,
        }

        if web_search_analyzed_runs:
            metrics.update(
                {
                    "target_source_presence_rate":
                        target_source_presence_rate,

                    "target_source_prompt_coverage":
                        target_source_prompt_coverage,

                    "grounded_target_mention_rate":
                        grounded_target_mention_rate,

                    "grounded_target_prompt_coverage":
                        grounded_target_prompt_coverage,

                    "target_grounded_response_share_of_voice":
                        target_grounded_response_share_of_voice,

                    "source_to_citation_conversion":
                        source_to_citation_conversion,

                    "target_source_to_citation_conversion":
                        target_source_to_citation_conversion,

                    "target_source_share_of_voice":
                        target_source_share_of_voice,

                    "target_citation_share_of_voice":
                        target_citation_share_of_voice,

                    "resolved_first_party_source_rate":
                        resolved_first_party_source_rate,

                    "web_visibility_score_v1":
                        web_visibility_score_v1,
                }
            )

        if persist_snapshot:

            snapshot_details = {
                "analyzed_prompts":
                    len(
                        analyzed_prompt_ids
                    ),

                "benchmark_mode":
                    benchmark_mode,

                "web_search_analyzed_runs":
                    web_search_analyzed_runs,

                "unique_search_source_urls":
                    unique_search_source_urls,

                "unique_search_domains":
                    unique_search_domains,
            }

            for metric_name, value in (
                metrics.items()
            ):

                if value is None:
                    continue

                MetricSnapshotRepository.create(
                    db=db,
                    project_id=project_id,
                    brand_id=target_brand.id,
                    metric_name=metric_name,
                    metric_value=value,
                    sample_size=(
                        web_search_analyzed_runs
                        if metric_name in {
                            "target_source_presence_rate",
                            "target_source_prompt_coverage",
                            "grounded_target_mention_rate",
                            "grounded_target_prompt_coverage",
                            "source_to_citation_conversion",
                            "target_source_to_citation_conversion",
                            "target_source_share_of_voice",
                            "target_citation_share_of_voice",
                            "resolved_first_party_source_rate",
                            "web_visibility_score_v1",
                        }
                        else analyzed_runs
                    ),
                    details=snapshot_details,
                    experiment_id=experiment_id,
                )

            db.commit()

        return {
            "project_id":
                project_id,

            "experiment_id":
                experiment_id,

            "benchmark_mode":
                benchmark_mode,

            "target_brand_id":
                target_brand.id,

            "target_brand":
                target_brand.name,

            "analyzed_runs":
                analyzed_runs,

            "analyzed_prompts":
                len(
                    analyzed_prompt_ids
                ),

            "web_search_analyzed_runs":
                web_search_analyzed_runs,

            "target_mention_count":
                target_mention_count,

            "mention_rate":
                mention_rate,

            "prompt_coverage":
                prompt_coverage,

            "citation_rate":
                citation_rate,

            "average_mention_position":
                average_position,

            "target_share_of_voice":
                target_sov,
            "target_response_share_of_voice":
                target_response_share_of_voice,
            "target_response_coverage":
                target_response_coverage,

            "position_quality":
                position_quality,

            "visibility_score_v1":
                visibility_score,

            "web_visibility_score_v1":
                web_visibility_score_v1,

            "target_grounded_response_share_of_voice":
                target_grounded_response_share_of_voice,

            "target_source_presence_rate":
                target_source_presence_rate,

            "target_source_prompt_coverage":
                target_source_prompt_coverage,

            "grounded_target_mention_rate":
                grounded_target_mention_rate,

            "grounded_target_prompt_coverage":
                grounded_target_prompt_coverage,

            "unique_search_source_urls":
                unique_search_source_urls,

            "unique_search_domains":
                unique_search_domains,

            "source_to_citation_conversion":
                source_to_citation_conversion,

            "target_source_to_citation_conversion":
                target_source_to_citation_conversion,

            "target_source_share_of_voice":
                target_source_share_of_voice,

            "target_citation_share_of_voice":
                target_citation_share_of_voice,

            "resolved_first_party_source_rate":
                resolved_first_party_source_rate,

            "share_of_voice":
                share_of_voice,
            "response_share_of_voice":
                response_share_of_voice,

            "grounded_response_share_of_voice":
                grounded_response_share_of_voice,
        }
