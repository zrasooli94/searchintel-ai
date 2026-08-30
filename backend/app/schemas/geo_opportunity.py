from pydantic import BaseModel, ConfigDict


class CompetitorEvidence(BaseModel):
    brand_id: int
    name: str
    run_coverage: float
    mention_count: int
    average_position: float


class GeoPromptOpportunityRead(BaseModel):
    id: int
    experiment_id: int
    project_id: int
    prompt_id: int
    target_brand_id: int

    prompt_text: str
    category: str
    intent: str | None

    run_count: int
    target_mention_runs: int
    target_mention_rate: float

    top_competitor_brand_id: int | None
    top_competitor_name: str | None
    top_competitor_run_coverage: float

    opportunity_score: float
    priority: str
    gap_type: str

    evidence: dict | None
    recommendation: str

    model_config = ConfigDict(
        from_attributes=True
    )


class GeoOpportunitySummary(BaseModel):
    experiment_id: int
    project_id: int
    target_brand_id: int
    target_brand: str
    analysis_status: str

    total_prompts: int

    high_priority: int
    medium_priority: int
    low_priority: int

    target_absent_prompts: int
    competitor_dominance_prompts: int
    covered_prompts: int
    unmeasured_prompts: int

    opportunities: list[
        GeoPromptOpportunityRead
    ]
