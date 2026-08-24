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
