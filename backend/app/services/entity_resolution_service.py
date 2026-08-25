from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ai_response import AIResponse
from app.models.ai_run import AIRun
from app.models.brand import Brand
from app.models.brand_mention import BrandMention
from app.models.project_brand import ProjectBrand

from app.repositories.entity_alias_repository import (
    EntityAliasRepository,
)
from app.repositories.entity_relationship_repository import (
    EntityRelationshipRepository,
)
from app.repositories.entity_resolution_rule_repository import (
    EntityResolutionRuleRepository,
)
from app.repositories.project_repository import (
    ProjectRepository,
)
from app.repositories.search_entity_repository import (
    SearchEntityRepository,
)

from app.services.brand_service import BrandService


class EntityResolutionService:

    COMPETITOR_ENTITY_TYPES = {
        "brand",
        "company",
    }

    @staticmethod
    def get_project_mentions(
        db: Session,
        project_id: int,
        normalized_name: str,
    ) -> list[BrandMention]:

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
                AIRun.project_id
                == project_id,
                BrandMention.normalized_name
                == normalized_name,
            )
        )

        return list(
            db.scalars(statement).all()
        )

    @staticmethod
    def get_or_create_competitor_brand(
        db: Session,
        project_id: int,
        name: str,
    ) -> Brand:

        normalized = (
            BrandService.normalize_name(
                name
            )
        )

        brand = db.scalar(
            select(Brand)
            .where(
                Brand.normalized_name
                == normalized
            )
        )

        if brand is None:
            brand = Brand(
                name=name,
                normalized_name=normalized,
                description=(
                    "Competitor discovered through "
                    "SearchIntel entity resolution."
                ),
            )

            db.add(brand)
            db.flush()

        link = db.scalar(
            select(ProjectBrand)
            .where(
                ProjectBrand.project_id
                == project_id,
                ProjectBrand.brand_id
                == brand.id,
            )
        )

        if link is None:
            db.add(
                ProjectBrand(
                    project_id=project_id,
                    brand_id=brand.id,
                    role="competitor",
                )
            )

            db.flush()

        return brand

    @classmethod
    def resolve_create(
        cls,
        db: Session,
        project_id: int,
        rule,
        item,
    ):

        if item.entity_type is None:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"rule_id={rule.id}: "
                    "entity_type is required "
                    "for action=create."
                ),
            )

        if (
            item.create_competitor_brand
            and item.entity_type
            not in cls.COMPETITOR_ENTITY_TYPES
        ):
            raise HTTPException(
                status_code=422,
                detail=(
                    f"rule_id={rule.id}: "
                    "only brand/company entities "
                    "can become competitor brands."
                ),
            )

        parent = None

        if item.parent_entity_id is not None:
            parent = (
                SearchEntityRepository.get_by_id(
                    db,
                    item.parent_entity_id,
                )
            )

            if parent is None:
                raise HTTPException(
                    status_code=404,
                    detail=(
                        "Parent entity not found: "
                        f"{item.parent_entity_id}"
                    ),
                )

            if item.relationship_type is None:
                raise HTTPException(
                    status_code=422,
                    detail=(
                        f"rule_id={rule.id}: "
                        "relationship_type is required "
                        "when parent_entity_id is set."
                    ),
                )

        elif item.relationship_type is not None:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"rule_id={rule.id}: "
                    "parent_entity_id is required "
                    "when relationship_type is set."
                ),
            )

        brand_id = None

        if item.create_competitor_brand:
            brand = (
                cls.get_or_create_competitor_brand(
                    db=db,
                    project_id=project_id,
                    name=(
                        rule.display_name
                        or rule.normalized_name
                    ),
                )
            )

            brand_id = brand.id

        elif parent is not None:
            brand_id = (
                parent.rollup_brand_id
            )

        existing = (
            SearchEntityRepository
            .get_by_normalized_name(
                db,
                rule.normalized_name,
                item.entity_type,
            )
        )

        if existing is not None:
            entity = existing

            if (
                entity.rollup_brand_id is None
                and brand_id is not None
            ):
                entity.rollup_brand_id = (
                    brand_id
                )

        else:
            entity = (
                SearchEntityRepository.create(
                    db=db,
                    name=(
                        rule.display_name
                        or rule.normalized_name
                    ),
                    normalized_name=(
                        rule.normalized_name
                    ),
                    entity_type=(
                        item.entity_type
                    ),
                    rollup_brand_id=brand_id,
                    description=(
                        "Entity discovered through "
                        "SearchIntel GEO analysis."
                    ),
                )
            )

        if parent is not None:
            (
                EntityRelationshipRepository
                .create_if_missing(
                    db=db,
                    subject_entity_id=entity.id,
                    object_entity_id=parent.id,
                    relationship_type=(
                        item.relationship_type
                    ),
                    confidence=1.0,
                    source="manual_resolution",
                )
            )

        return entity

    @staticmethod
    def resolve_merge(
        db: Session,
        rule,
        item,
    ):

        if item.canonical_entity_id is None:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"rule_id={rule.id}: "
                    "canonical_entity_id is required "
                    "for action=merge."
                ),
            )

        entity = (
            SearchEntityRepository.get_by_id(
                db,
                item.canonical_entity_id,
            )
        )

        if entity is None:
            raise HTTPException(
                status_code=404,
                detail=(
                    "Canonical entity not found: "
                    f"{item.canonical_entity_id}"
                ),
            )

        if (
            rule.normalized_name
            != entity.normalized_name
        ):
            EntityAliasRepository.create_if_missing(
                db=db,
                entity_id=entity.id,
                alias=(
                    rule.display_name
                    or rule.normalized_name
                ),
                normalized_alias=(
                    rule.normalized_name
                ),
            )

        return entity

    @classmethod
    def resolve(
        cls,
        db: Session,
        project_id: int,
        items,
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

        resolved_items = []

        try:
            for item in items:

                rule = (
                    EntityResolutionRuleRepository
                    .get_by_id(
                        db,
                        item.rule_id,
                    )
                )

                if rule is None:
                    raise HTTPException(
                        status_code=404,
                        detail=(
                            "Resolution rule not found: "
                            f"{item.rule_id}"
                        ),
                    )

                if rule.project_id != project_id:
                    raise HTTPException(
                        status_code=422,
                        detail=(
                            f"rule_id={rule.id} does "
                            "not belong to this project."
                        ),
                    )

                identity_match = (
                    ProjectBrandRepository
                    .find_identity_match(
                        db=db,
                        project_id=project_id,
                        normalized_name=(
                            rule.normalized_name
                        ),
                    )
                )

                if identity_match is not None:
                    matched_brand, role = (
                        identity_match
                    )

                    raise HTTPException(
                        status_code=422,
                        detail=(
                            f"rule_id={rule.id}: "
                            "registered project identity "
                            "cannot be resolved through "
                            "the candidate entity workflow "
                            f"({matched_brand.name}, "
                            f"role={role})."
                        ),
                    )

                if rule.status not in {
                    "candidate",
                    "resolved",
                }:
                    raise HTTPException(
                        status_code=422,
                        detail=(
                            f"rule_id={rule.id} has "
                            f"status={rule.status}; "
                            "only candidate/resolved "
                            "rules may be resolved."
                        ),
                    )

                if item.action == "create":
                    entity = cls.resolve_create(
                        db=db,
                        project_id=project_id,
                        rule=rule,
                        item=item,
                    )

                elif item.action == "merge":
                    if item.create_competitor_brand:
                        raise HTTPException(
                            status_code=422,
                            detail=(
                                f"rule_id={rule.id}: "
                                "merge cannot create "
                                "a competitor brand."
                            ),
                        )

                    entity = cls.resolve_merge(
                        db=db,
                        rule=rule,
                        item=item,
                    )

                else:
                    raise HTTPException(
                        status_code=422,
                        detail="Unsupported action.",
                    )

                brand_id = (
                    entity.rollup_brand_id
                )

                mentions = (
                    cls.get_project_mentions(
                        db=db,
                        project_id=project_id,
                        normalized_name=(
                            rule.normalized_name
                        ),
                    )
                )

                for mention in mentions:
                    if mention.is_target:
                        continue

                    if (
                        mention.resolution_status
                        == "lexical_match"
                    ):
                        continue

                    if rule.status == "candidate":
                        if (
                            mention.resolution_status
                            not in {
                                "unresolved",
                                "candidate",
                            }
                        ):
                            continue

                    elif rule.status == "resolved":
                        if (
                            mention.resolution_status
                            != "resolved"
                        ):
                            continue

                        if (
                            rule.entity_id is not None
                            and mention.entity_id
                            != rule.entity_id
                        ):
                            continue

                    mention.entity_id = entity.id
                    mention.brand_id = brand_id
                    mention.resolution_status = (
                        "resolved"
                    )
                    mention.confidence = 1.0
                    mention.is_target = False

                (
                    EntityResolutionRuleRepository
                    .upsert(
                        db=db,
                        project_id=project_id,
                        normalized_name=(
                            rule.normalized_name
                        ),
                        display_name=(
                            rule.display_name
                        ),
                        status="resolved",
                        brand_id=brand_id,
                        entity_id=entity.id,
                        entity_type=(
                            entity.entity_type
                        ),
                        confidence=1.0,
                        source="manual_entity_resolution",
                    )
                )

                resolved_items.append(
                    {
                        "rule_id":
                            rule.id,
                        "entity_id":
                            entity.id,
                        "name":
                            entity.name,
                        "entity_type":
                            entity.entity_type,
                        "brand_id":
                            brand_id,
                        "action":
                            item.action,
                    }
                )

            db.commit()

        except Exception:
            db.rollback()
            raise

        return {
            "project_id":
                project_id,
            "resolved_count":
                len(resolved_items),
            "items":
                resolved_items,
        }
