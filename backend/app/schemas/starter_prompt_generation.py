from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator


MeasurementScope = Literal["brand_wide", "focused"]


class StarterPromptGenerateRequest(BaseModel):
    count: int = Field(
        default=19,
        ge=8,
        le=20,
    )

    model_id: int | None = None
    measurement_scope: MeasurementScope = "brand_wide"
    focus_label: str | None = Field(default=None, max_length=255)

    @model_validator(mode="after")
    def validate_focus(self):
        if self.measurement_scope == "focused" and not (self.focus_label or "").strip():
            raise ValueError("A focus label is required for focused measurement scope.")
        return self


class StarterPromptSuggestion(BaseModel):
    text: str
    category: str
    topic_cluster: str
    rationale: str | None = None


class TopicCluster(BaseModel):
    name: str
    evidence: list[str]
    allocated_prompts: int


class CoverageBlueprint(BaseModel):
    topic_distribution: dict[str, int]
    intent_distribution: dict[str, int]
    largest_topic_share: float
    concentration_status: Literal["balanced", "needs_review", "focused"]


class StarterPromptGenerationResult(BaseModel):
    id: int
    project_id: int
    status: str
    generator_version: str
    measurement_scope: MeasurementScope
    focus_label: str | None

    model_id: int | None = None
    model_name: str
    provider_model_id: str | None = None

    target_brand: str

    website_pages_used: int
    competitors_used: list[str]
    existing_prompts_considered: int

    requested_count: int
    generated_count: int

    topic_clusters: list[TopicCluster]
    coverage_blueprint: CoverageBlueprint
    warnings: list[str]

    prompts: list[
        StarterPromptSuggestion
    ]
    created_at: datetime


class PromptProposalApplyRequest(BaseModel):
    prompts: list[StarterPromptSuggestion] | None = Field(default=None, max_length=20)


class PromptProposalApplyResult(BaseModel):
    project_id: int
    proposal_id: int
    active_prompt_count: int
    active_prompt_ids: list[int]
