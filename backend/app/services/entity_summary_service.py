from collections import defaultdict

from fastapi import HTTPException
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.brand import Brand
from app.models.entity_alias import EntityAlias
from app.models.entity_relationship import (
    EntityRelationship,
)
from app.models.project_brand import ProjectBrand
from app.models.search_entity import SearchEntity

from app.repositories.entity_resolution_rule_repository import (
    EntityResolutionRuleRepository,
)
from app.repositories.project_repository import (
    ProjectRepository,
)


class EntitySummaryService:

    TYPE_ORDER = {
        "brand": 1,
        "company": 2,
        "product": 3,
        "service": 4,
        "software_project": 5,
        "organization": 6,
    }

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

        # ---------------------------------------------
        # Project brand scope
        # ---------------------------------------------

        project_brand_rows = list(
            db.execute(
                select(
                    ProjectBrand,
                    Brand,
                )
                .join(
                    Brand,
                    Brand.id
                    == ProjectBrand.brand_id,
                )
                .where(
                    ProjectBrand.project_id
                    == project_id,
                )
            ).all()
        )

        project_brand_ids = {
            brand.id
            for _link, brand
            in project_brand_rows
        }

        brand_names = {
            brand.id: brand.name
            for _link, brand
            in project_brand_rows
        }

        brand_roles = {
            brand.id: link.role
            for link, brand
            in project_brand_rows
        }

        # ---------------------------------------------
        # Resolution knowledge
        # ---------------------------------------------

        candidate_rules = (
            EntityResolutionRuleRepository
            .list_by_status(
                db,
                project_id,
                "candidate",
            )
        )

        resolved_rules = (
            EntityResolutionRuleRepository
            .list_by_status(
                db,
                project_id,
                "resolved",
            )
        )

        rejected_rules = (
            EntityResolutionRuleRepository
            .list_by_status(
                db,
                project_id,
                "rejected",
            )
        )

        resolved_entity_ids = {
            rule.entity_id
            for rule in resolved_rules
            if rule.entity_id is not None
        }

        # ---------------------------------------------
        # Project-scoped canonical entities
        # ---------------------------------------------

        filters = []

        if project_brand_ids:
            filters.append(
                SearchEntity.rollup_brand_id.in_(
                    project_brand_ids
                )
            )

        if resolved_entity_ids:
            filters.append(
                SearchEntity.id.in_(
                    resolved_entity_ids
                )
            )

        if not filters:
            entities = []
        else:
            entities = list(
                db.scalars(
                    select(SearchEntity)
                    .where(
                        or_(*filters)
                    )
                ).all()
            )

        entity_ids = {
            entity.id
            for entity in entities
        }

        entity_by_id = {
            entity.id: entity
            for entity in entities
        }

        # ---------------------------------------------
        # Aliases
        # ---------------------------------------------

        alias_rows = []

        if entity_ids:
            alias_rows = list(
                db.scalars(
                    select(EntityAlias)
                    .where(
                        EntityAlias.entity_id.in_(
                            entity_ids
                        )
                    )
                    .order_by(
                        EntityAlias.alias
                    )
                ).all()
            )

        aliases_by_entity = defaultdict(list)

        for alias in alias_rows:
            aliases_by_entity[
                alias.entity_id
            ].append(
                alias.alias
            )

        # ---------------------------------------------
        # Relationships
        #
        # Both sides must belong to this project's
        # scoped entity set.
        # ---------------------------------------------

        relationship_rows = []

        if entity_ids:
            relationship_rows = list(
                db.scalars(
                    select(
                        EntityRelationship
                    )
                    .where(
                        EntityRelationship
                        .subject_entity_id
                        .in_(entity_ids),

                        EntityRelationship
                        .object_entity_id
                        .in_(entity_ids),
                    )
                    .order_by(
                        EntityRelationship.id
                    )
                ).all()
            )

        relationships = []

        parents_by_entity = defaultdict(list)
        children_by_entity = defaultdict(list)

        for relationship in relationship_rows:

            subject = entity_by_id[
                relationship.subject_entity_id
            ]

            object_entity = entity_by_id[
                relationship.object_entity_id
            ]

            item = {
                "id":
                    relationship.id,

                "subject_entity_id":
                    subject.id,

                "subject_name":
                    subject.name,

                "subject_type":
                    subject.entity_type,

                "relationship_type":
                    relationship.relationship_type,

                "object_entity_id":
                    object_entity.id,

                "object_name":
                    object_entity.name,

                "object_type":
                    object_entity.entity_type,

                "confidence":
                    relationship.confidence,

                "source":
                    relationship.source,
            }

            relationships.append(
                item
            )

            parents_by_entity[
                subject.id
            ].append(
                item
            )

            children_by_entity[
                object_entity.id
            ].append(
                item
            )

        # ---------------------------------------------
        # Entity registry
        # ---------------------------------------------

        entity_items = []

        for entity in entities:

            entity_items.append(
                {
                    "id":
                        entity.id,

                    "name":
                        entity.name,

                    "normalized_name":
                        entity.normalized_name,

                    "entity_type":
                        entity.entity_type,

                    "rollup_brand_id":
                        entity.rollup_brand_id,

                    "rollup_brand":
                        brand_names.get(
                            entity.rollup_brand_id
                        ),

                    "project_role":
                        brand_roles.get(
                            entity.rollup_brand_id
                        ),

                    "description":
                        entity.description,

                    "aliases":
                        aliases_by_entity.get(
                            entity.id,
                            [],
                        ),

                    "parent_relationships":
                        parents_by_entity.get(
                            entity.id,
                            [],
                        ),

                    "child_relationships":
                        children_by_entity.get(
                            entity.id,
                            [],
                        ),
                }
            )

        entity_items.sort(
            key=lambda item: (
                cls.TYPE_ORDER.get(
                    item["entity_type"],
                    99,
                ),
                item["name"].lower(),
            )
        )

        # ---------------------------------------------
        # Candidate review queue
        # ---------------------------------------------

        candidates = [
            {
                "rule_id":
                    rule.id,

                "name":
                    (
                        rule.display_name
                        or rule.normalized_name
                    ),

                "normalized_name":
                    rule.normalized_name,

                "entity_type":
                    rule.entity_type,

                "proposed_parent_name":
                    rule.proposed_parent_name,

                "proposed_relationship_type":
                    rule.proposed_relationship_type,

                "classification_confidence":
                    rule.classification_confidence,

                "classification_source":
                    rule.classification_source,
            }
            for rule in candidate_rules
        ]

        candidates.sort(
            key=lambda item: (
                -(
                    item[
                        "classification_confidence"
                    ]
                    or 0.0
                ),
                item["name"].lower(),
            )
        )

        def count_type(
            entity_type: str,
        ) -> int:
            return sum(
                entity.entity_type
                == entity_type
                for entity in entities
            )

        return {
            "project_id":
                project_id,

            "stats": {
                "total_entities":
                    len(entities),

                "brands":
                    count_type("brand"),

                "companies":
                    count_type("company"),

                "products":
                    count_type("product"),

                "software_projects":
                    count_type(
                        "software_project"
                    ),

                "organizations":
                    count_type(
                        "organization"
                    ),

                "services":
                    count_type("service"),

                "aliases":
                    len(alias_rows),

                "relationships":
                    len(
                        relationship_rows
                    ),

                "candidates":
                    len(candidate_rules),

                "resolved_rules":
                    len(resolved_rules),

                "rejected_rules":
                    len(rejected_rules),
            },

            "entities":
                entity_items,

            "relationships":
                relationships,

            "candidates":
                candidates,
        }
