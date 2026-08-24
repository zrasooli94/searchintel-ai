from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


class GeoActionPlanRequest(BaseModel):
    model_id: int

    priorities: list[str] = [
        "high",
        "medium",
    ]

    max_actions: int = Field(
        default=8,
        ge=3,
        le=12,
    )


class GeoActionItemRead(BaseModel):
    id: int
    action_plan_id: int
    sort_order: int

    priority: str
    action_type: str

    title: str
    rationale: str

    target_page: str | None

    impacted_prompt_ids: list[int]
    impacted_opportunity_ids: list[int]

    implementation_steps: list
    evidence: list
    success_metrics: list
    dependencies: list

    effort: str
    status: str

    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )


class GeoActionPlanRead(BaseModel):
    id: int

    experiment_id: int
    project_id: int
    target_brand_id: int
    model_id: int

    status: str
    strategy_summary: str

    baseline_metrics: dict
    source_diagnosis_ids: list[int]

    recommended_sequence: list
    risks_and_limits: list

    created_at: datetime

    actions: list[GeoActionItemRead]
