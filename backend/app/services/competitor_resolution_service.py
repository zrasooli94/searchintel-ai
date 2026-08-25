from collections import defaultdict

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ai_response import AIResponse
from app.models.ai_run import AIRun
from app.models.brand_mention import BrandMention
from app.repositories.brand_repository import BrandRepository
from app.repositories.entity_resolution_rule_repository import (
    EntityResolutionRuleRepository,
)
from app.repositories.project_brand_repository import (
    ProjectBrandRepository,
)
from app.repositories.project_repository import (
    ProjectRepository,
)
from app.repositories.search_entity_repository import (
    SearchEntityRepository,
)
from app.services.brand_service import BrandService


class CompetitorResolutionService:

    @staticmethod
    def list_candidates(
        db: Session,
        project_id: int,
    ) -> list[dict]:
        project = ProjectRepository.get_by_id(
            db,
            project_id,
        )

        if project is None:
            raise HTTPException(
                status_code=404,
                detail="Project not found.",
            )

        statement = (
            select(BrandMention)
            .join(
                AIResponse,
                BrandMention.response_id
                == AIResponse.id,
            )
            .join(
                AIRun,
                AIResponse.run_id
                == AIRun.id,
            )
            .where(
                AIRun.project_id == project_id,
                BrandMention.resolution_status.in_(
                    ["unresolved", "candidate"]
                ),
            )
        )

        mentions = list(
            db.scalars(statement).all()
        )

        grouped: dict[str, dict] = {}

        response_sets = defaultdict(set)

        for mention in mentions:
            key = mention.normalized_name

            if key not in grouped:
                grouped[key] = {
                    "name": mention.mention_text,
                    "normalized_name": key,
                    "mention_count": 0,
                    "confidence": mention.confidence,
                }

            grouped[key]["mention_count"] += (
                mention.mention_count
            )

            grouped[key]["confidence"] = max(
                grouped[key]["confidence"],
                mention.confidence,
            )

            response_sets[key].add(
                mention.response_id
            )

        results = []

        for key, item in grouped.items():
            item["response_count"] = len(
                response_sets[key]
            )

            results.append(item)

        return sorted(
            results,
            key=lambda item: (
                -item["response_count"],
                -item["mention_count"],
                item["name"].lower(),
            ),
        )

    @staticmethod
    def resolve(
        db: Session,
        project_id: int,
        names: list[str],
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

        resolved = []

        for requested_name in names:
            normalized = BrandService.normalize_name(
                requested_name
            )

            identity_match = (
                ProjectBrandRepository
                .find_identity_match(
                    db=db,
                    project_id=project_id,
                    normalized_name=normalized,
                )
            )

            if identity_match is not None:
                matched_brand, role = identity_match

                raise HTTPException(
                    status_code=422,
                    detail=(
                        f"{requested_name} matches a "
                        "registered project identity "
                        f"({matched_brand.name}, "
                        f"role={role}) and cannot be "
                        "resolved through the competitor "
                        "candidate workflow."
                    ),
                )


            statement = (
                select(BrandMention)
                .join(
                    AIResponse,
                    BrandMention.response_id
                    == AIResponse.id,
                )
                .join(
                    AIRun,
                    AIResponse.run_id
                    == AIRun.id,
                )
                .where(
                    AIRun.project_id == project_id,
                    BrandMention.normalized_name
                    == normalized,
                    BrandMention.resolution_status.in_(
                        (
                            "unresolved",
                            "candidate",
                        )
                    ),
                    BrandMention.is_target.is_(False),
                )
            )

            mentions = list(
                db.scalars(statement).all()
            )

            if not mentions:
                continue

            display_name = mentions[
                0
            ].mention_text

            brand = (
                BrandRepository.get_by_normalized_name(
                    db,
                    normalized,
                )
            )

            if brand is None:
                brand = BrandRepository.create(
                    db=db,
                    name=display_name,
                    normalized_name=normalized,
                    description=(
                        "Competitor discovered through "
                        "SearchIntel GEO analysis."
                    ),
                )

            entity = (
                SearchEntityRepository
                .get_brand_entity_by_brand_id(
                    db,
                    brand.id,
                )
            )

            if entity is None:
                entity = (
                    SearchEntityRepository.create(
                        db=db,
                        name=brand.name,
                        normalized_name=(
                            brand.normalized_name
                        ),
                        entity_type="brand",
                        rollup_brand_id=brand.id,
                        description=(
                            brand.description
                        ),
                    )
                )

            link = ProjectBrandRepository.get_link(
                db,
                project_id,
                brand.id,
            )

            if link is None:
                link = ProjectBrandRepository.create(
                    db=db,
                    project_id=project_id,
                    brand_id=brand.id,
                    role="competitor",
                )

            for mention in mentions:
                mention.brand_id = brand.id
                mention.entity_id = entity.id
                mention.resolution_status = "resolved"
                mention.confidence = 1.0

            EntityResolutionRuleRepository.upsert(
                db=db,
                project_id=project_id,
                normalized_name=normalized,
                display_name=display_name,
                status="resolved",
                brand_id=brand.id,
                entity_id=entity.id,
                entity_type="brand",
                confidence=1.0,
                source="manual_resolution",
            )

            resolved.append(
                {
                    "brand_id": brand.id,
                    "name": brand.name,
                    "normalized_name":
                        brand.normalized_name,
                    "role": link.role,
                }
            )

        db.commit()

        return {
            "project_id": project_id,
            "resolved_count": len(resolved),
            "competitors": resolved,
        }
