from pydantic import BaseModel


class ShareOfVoiceItem(BaseModel):
    brand_id: int | None
    name: str
    mention_count: int
    share_of_voice: float


class ResponseShareOfVoiceItem(BaseModel):
    brand_id: int
    name: str

    response_exposures: int
    response_share_of_voice: float
    response_coverage: float


class GroundedResponseShareOfVoiceItem(BaseModel):
    brand_id: int
    name: str

    grounded_response_exposures: int
    grounded_response_share_of_voice: float
    grounded_response_coverage: float


class SourceExposureShareOfVoiceItem(BaseModel):
    brand_id: int
    name: str

    source_exposures: int
    source_exposure_share_of_voice: float


class CitationExposureShareOfVoiceItem(BaseModel):
    brand_id: int
    name: str

    citation_exposures: int
    citation_exposure_share_of_voice: float


class BrandCitationConversionItem(BaseModel):
    brand_id: int
    name: str

    source_exposures: int
    citation_exposures: int

    citation_exposure_conversion: float


class CitedResponseShareOfVoiceItem(BaseModel):
    brand_id: int
    name: str

    cited_response_exposures: int
    cited_response_share_of_voice: float
    cited_response_coverage: float


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

    # Web-search entity verification.
    entity_verified_target_mention_count: int
    entity_verified_target_mention_rate: float | None
    entity_verified_target_prompt_coverage: float | None
    entity_verified_target_share_of_voice: float | None

    mention_rate: float
    prompt_coverage: float
    citation_rate: float

    average_mention_position: float | None

    # Mention-frequency SOV.
    target_share_of_voice: float

    # Hierarchy-safe brand exposure metrics.
    target_response_share_of_voice: float
    target_response_coverage: float

    position_quality: float
    visibility_score_v1: float
    web_visibility_score_v1: float | None

    # Web-search-only metrics.
    # Null means no eligible web-search runs
    # were present in this measurement set.
    target_source_presence_rate: float | None
    target_source_prompt_coverage: float | None

    grounded_target_mention_rate: float | None
    grounded_target_prompt_coverage: float | None

    # Hierarchy-safe web-grounded exposure.
    # V1 retrieval-associated metric:
    # textual mention + same-brand source retrieved.
    target_grounded_response_share_of_voice: float | None

    # Stronger evidence-used metric:
    # textual mention + same-brand citation.
    target_cited_response_share_of_voice: float | None
    target_cited_response_coverage: float | None

    unique_search_source_urls: int
    unique_search_domains: int

    source_to_citation_conversion: float | None
    target_source_to_citation_conversion: float | None

    target_source_share_of_voice: float | None
    target_citation_share_of_voice: float | None

    # Per-response URL exposure SOV.
    target_source_exposure_share_of_voice: float | None
    target_citation_exposure_share_of_voice: float | None

    # Null when target has zero source exposures.
    target_citation_exposure_conversion: float | None

    resolved_first_party_source_rate: float | None

    # Frequency-based leaderboard.
    share_of_voice: list[
        ShareOfVoiceItem
    ]

    # One exposure per brand per response.
    response_share_of_voice: list[
        ResponseShareOfVoiceItem
    ]

    # One grounded exposure per brand
    # per web-search response.
    # Retained V1 name for backward compatibility.
    # Semantically this is retrieval-associated.
    grounded_response_share_of_voice: list[
        GroundedResponseShareOfVoiceItem
    ]

    cited_response_share_of_voice: list[
        CitedResponseShareOfVoiceItem
    ]

    source_exposure_share_of_voice: list[
        SourceExposureShareOfVoiceItem
    ]

    citation_exposure_share_of_voice: list[
        CitationExposureShareOfVoiceItem
    ]

    brand_citation_conversion: list[
        BrandCitationConversionItem
    ]
