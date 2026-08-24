from typing import Literal

from pydantic import BaseModel, Field


class EntityClassificationRequest(BaseModel):
    model_id: int
    limit: int = Field(
        default=100,
        ge=1,
        le=250,
    )


class EntityClassificationItem(BaseModel):
    rule_id: int
    name: str
    normalized_name: str

    entity_type: str

    proposed_parent_name: str | None
    proposed_relationship_type: str | None

    confidence: float


class EntityClassificationResult(BaseModel):
    project_id: int
    model_id: int

    classified_count: int
    skipped_count: int

    classifications: list[
        EntityClassificationItem
    ]


class EntityCandidateRead(BaseModel):
    rule_id: int
    name: str
    normalized_name: str
    status: str

    entity_type: str | None

    proposed_parent_name: str | None
    proposed_relationship_type: str | None

    classification_confidence: float | None
    classification_source: str | None



class ResolveEntityItem(BaseModel):
    rule_id: int

    action: Literal[
        "create",
        "merge",
    ]

    entity_type: Literal[
        "brand",
        "company",
        "product",
        "software_project",
        "organization",
        "service",
    ] | None = None

    canonical_entity_id: int | None = None

    parent_entity_id: int | None = None

    relationship_type: Literal[
        "product_of",
        "owned_by",
        "operated_by",
        "service_of",
        "related_to",
        "brand_of",
    ] | None = None

    create_competitor_brand: bool = False


class ResolveEntitiesRequest(BaseModel):
    items: list[ResolveEntityItem]


class ResolvedEntityItem(BaseModel):
    rule_id: int
    entity_id: int
    name: str
    entity_type: str

    brand_id: int | None
    action: str


class ResolveEntitiesResult(BaseModel):
    project_id: int
    resolved_count: int
    items: list[ResolvedEntityItem]
