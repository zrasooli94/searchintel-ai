from collections import defaultdict

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ai_response import AIResponse
from app.models.ai_run import AIRun
from app.models.brand import Brand
from app.models.brand_mention import BrandMention
from app.models.citation import Citation
from app.repositories.metric_snapshot_repository import (
    MetricSnapshotRepository,
)
from app.repositories.project_brand_repository import (
    ProjectBrandRepository,
)
from app.repositories.project_repository import (
    ProjectRepository,
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
                detail=(
                    "Project has no target brand."
                ),
            )

        target_brand = target_rows[0][0]

        response_statement = (
            select(
                AIResponse.id,
                AIRun.prompt_id,
            )
            .join(
                AIRun,
                AIResponse.run_id
                == AIRun.id,
            )
            .where(
                AIRun.project_id == project_id,
                AIResponse.visibility_analyzed_at
                .is_not(None),
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

        analyzed_runs = len(
            response_ids
        )

        analyzed_prompt_ids = set(
            response_to_prompt.values()
        )

        target_statement = (
            select(BrandMention)
            .where(
                BrandMention.response_id.in_(
                    response_ids
                ),
                BrandMention.brand_id
                == target_brand.id,
            )
        )

        target_mentions = list(
            db.scalars(
                target_statement
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

        citation_statement = (
            select(Citation)
            .where(
                Citation.response_id.in_(
                    response_ids
                ),
                Citation.brand_id
                == target_brand.id,
            )
        )

        target_citations = list(
            db.scalars(
                citation_statement
            ).all()
        )

        cited_response_ids = {
            citation.response_id
            for citation in target_citations
        }

        citation_rate = cls.percent(
            len(cited_response_ids),
            analyzed_runs,
        )

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
                    100.0
                    / average_position,
                ),
                2,
            )

        all_mentions_statement = (
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
                BrandMention.brand_id.is_not(None),
            )
        )

        all_mentions = list(
            db.execute(
                all_mentions_statement
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
            if mention.brand_id is not None:
                key = f"brand:{mention.brand_id}"
                name = (
                    brand_name
                    or mention.mention_text
                )
            else:
                key = (
                    "unresolved:"
                    + mention.normalized_name
                )
                name = mention.mention_text

            grouped[key]["brand_id"] = (
                mention.brand_id
            )

            grouped[key]["name"] = name

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

        visibility_score = round(
            (
                mention_rate * 0.50
                + citation_rate * 0.20
                + prompt_coverage * 0.20
                + position_quality * 0.10
            ),
            2,
        )

        metrics = {
            "mention_rate": mention_rate,
            "prompt_coverage":
                prompt_coverage,
            "citation_rate":
                citation_rate,
            "target_share_of_voice":
                target_sov,
            "visibility_score_v1":
                visibility_score,
        }

        for metric_name, value in metrics.items():
            MetricSnapshotRepository.create(
                db=db,
                project_id=project_id,
                brand_id=target_brand.id,
                metric_name=metric_name,
                metric_value=value,
                sample_size=analyzed_runs,
                details={
                    "analyzed_prompts":
                        len(
                            analyzed_prompt_ids
                        )
                },
            )

        db.commit()

        return {
            "project_id": project_id,
            "target_brand_id":
                target_brand.id,
            "target_brand":
                target_brand.name,

            "analyzed_runs":
                analyzed_runs,
            "analyzed_prompts":
                len(analyzed_prompt_ids),

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

            "position_quality":
                position_quality,

            "visibility_score_v1":
                visibility_score,

            "share_of_voice":
                share_of_voice,
        }
