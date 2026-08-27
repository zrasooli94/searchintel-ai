from pydantic import BaseModel, ConfigDict


class SiteRAGGapRead(BaseModel):
    id: int
    experiment_id: int
    project_id: int
    prompt_id: int
    target_brand_id: int

    prompt_text: str
    category: str
    intent: str | None

    run_count: int
    answerable_runs: int
    unsupported_runs: int

    answerability_rate: float
    unsupported_rate: float

    gap_type: str
    gap_score: float
    priority: str

    evidence: dict
    recommendation: str

    model_config = ConfigDict(
        from_attributes=True
    )


class SiteRAGGapSummary(BaseModel):
    experiment_id: int
    project_id: int
    target_brand_id: int
    target_brand: str

    total_prompts: int
    gap_prompts: int
    covered_prompts: int

    high_priority: int
    medium_priority: int
    low_priority: int

    gap_type_counts: dict[str, int]

    site_answerability_rate_v1: float | None
    unsupported_answer_rate_v1: float | None
    evidence_coverage_rate: float | None
    source_reference_rate: float | None
    evidence_utilization_rate: float | None

    gaps: list[SiteRAGGapRead]
