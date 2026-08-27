from datetime import datetime

from pydantic import BaseModel


class SiteRAGSupportingPage(BaseModel):
    page_id: int | None
    url: str
    title: str | None

    response_count: int
    reference_count: int


class ExperimentSummaryItem(BaseModel):
    id: int
    name: str

    phase: str
    status: str
    benchmark_mode: str

    runs: int
    prompts: int

    analysis_version: str
    analysis_total_responses: int
    analysis_current_responses: int
    analysis_stale_responses: int
    analysis_is_current: bool

    mention_rate: float
    prompt_coverage: float
    entity_verified_target_mention_rate: float | None
    entity_verified_target_prompt_coverage: float | None
    entity_verified_target_share_of_voice: float | None
    citation_rate: float

    visibility_score_v1: float
    web_visibility_score_v1: float | None

    site_rag_analyzed_runs: int
    site_rag_analyzed_prompts: int

    evidence_coverage_rate: float | None
    source_reference_rate: float | None
    evidence_utilization_rate: float | None

    site_answerability_rate_v1: float | None
    unsupported_answer_rate_v1: float | None

    unique_supporting_pages: int
    unique_supporting_urls: int

    avg_sources_per_response: float | None

    top_supporting_pages: list[
        SiteRAGSupportingPage
    ]

    target_response_coverage: float
    grounded_target_mention_rate: float | None
    target_cited_response_coverage: float | None
    target_source_presence_rate: float | None

    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime


class ComparableExperimentPair(BaseModel):
    baseline_id: int
    baseline_name: str

    comparison_id: int
    comparison_name: str

    benchmark_mode: str


class ExperimentsSummary(BaseModel):
    project_id: int

    total_experiments: int
    completed_experiments: int
    draft_experiments: int

    experiments: list[
        ExperimentSummaryItem
    ]

    comparable_pairs: list[
        ComparableExperimentPair
    ]
