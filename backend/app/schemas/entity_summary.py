from pydantic import BaseModel


class EntitySummaryRelationship(BaseModel):
    id: int

    subject_entity_id: int
    subject_name: str
    subject_type: str

    relationship_type: str

    object_entity_id: int
    object_name: str
    object_type: str

    confidence: float
    source: str


class EntitySummaryItem(BaseModel):
    id: int

    name: str
    normalized_name: str
    entity_type: str

    rollup_brand_id: int | None
    rollup_brand: str | None
    project_role: str | None

    description: str | None

    aliases: list[str]

    parent_relationships: list[
        EntitySummaryRelationship
    ]

    child_relationships: list[
        EntitySummaryRelationship
    ]


class EntitySummaryCandidate(BaseModel):
    rule_id: int

    name: str
    normalized_name: str

    entity_type: str | None

    proposed_parent_name: str | None
    proposed_relationship_type: str | None

    classification_confidence: float | None
    classification_source: str | None


class EntitySummaryStats(BaseModel):
    total_entities: int

    brands: int
    companies: int
    products: int
    software_projects: int
    organizations: int
    services: int

    aliases: int
    relationships: int

    candidates: int
    resolved_rules: int
    rejected_rules: int


class EntitiesSummary(BaseModel):
    project_id: int

    stats: EntitySummaryStats

    entities: list[
        EntitySummaryItem
    ]

    relationships: list[
        EntitySummaryRelationship
    ]

    candidates: list[
        EntitySummaryCandidate
    ]
