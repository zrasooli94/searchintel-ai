from datetime import datetime

from pydantic import BaseModel


class ActionPlanSummaryItem(BaseModel):
    id: int
    sort_order: int

    priority: str
    action_type: str

    title: str
    rationale: str

    target_page: str | None

    impacted_prompt_ids: list[int]
    impacted_opportunity_ids: list[int]

    implementation_steps: list[str]
    evidence: list[str]
    success_metrics: list[str]
    dependencies: list[str]

    effort: str
    status: str


class ActionPlanSummary(BaseModel):
    project_id: int

    plan_id: int

    experiment_id: int
    experiment_name: str
    experiment_phase: str
    experiment_status: str
    benchmark_mode: str

    target_brand_id: int
    target_brand: str

    plan_status: str
    created_at: datetime

    strategy_summary: str

    baseline_metrics: dict

    recommended_sequence: list[str]
    risks_and_limits: list[str]

    total_actions: int
    open_actions: int
    completed_actions: int

    high_priority_actions: int
    medium_priority_actions: int
    low_priority_actions: int

    action_type_counts: dict[str, int]

    provenance_note: str

    actions: list[
        ActionPlanSummaryItem
    ]
