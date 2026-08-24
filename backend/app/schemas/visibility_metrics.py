from pydantic import BaseModel


class ShareOfVoiceItem(BaseModel):
    brand_id: int | None
    name: str
    mention_count: int
    share_of_voice: float


class AIVisibilityMetrics(BaseModel):
    project_id: int
    experiment_id: int | None = None

    benchmark_mode: str

    target_brand_id: int
    target_brand: str

    analyzed_runs: int
    analyzed_prompts: int
    web_search_analyzed_runs: int

    target_mention_count: int

    mention_rate: float
    prompt_coverage: float
    citation_rate: float

    average_mention_position: float | None
    target_share_of_voice: float

    position_quality: float
    visibility_score_v1: float

    # Web-search-only metrics.
    # Null means no eligible web-search runs
    # were present in this measurement set.
    target_source_presence_rate: float | None
    target_source_prompt_coverage: float | None

    unique_search_source_urls: int
    unique_search_domains: int

    source_to_citation_conversion: float | None
    target_source_to_citation_conversion: float | None

    target_source_share_of_voice: float | None
    target_citation_share_of_voice: float | None

    resolved_first_party_source_rate: float | None

    share_of_voice: list[ShareOfVoiceItem]
