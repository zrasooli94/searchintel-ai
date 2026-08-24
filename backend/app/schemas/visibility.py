from pydantic import BaseModel, ConfigDict


class BrandMentionRead(BaseModel):
    id: int
    response_id: int
    brand_id: int | None
    entity_id: int | None
    mention_text: str
    normalized_name: str
    position: int
    mention_count: int
    is_target: bool
    resolution_status: str
    confidence: float

    model_config = ConfigDict(
        from_attributes=True
    )


class CitationRead(BaseModel):
    id: int
    response_id: int
    brand_id: int | None
    entity_id: int | None
    url: str
    domain: str | None
    title: str | None
    position: int

    model_config = ConfigDict(
        from_attributes=True
    )


class WebSearchSourceRead(BaseModel):
    id: int
    response_id: int
    brand_id: int | None
    entity_id: int | None
    search_call_index: int
    source_position: int
    search_query: str | None
    url: str
    domain: str | None
    title: str | None
    is_cited: bool

    model_config = ConfigDict(
        from_attributes=True
    )


class VisibilityAnalysisRead(BaseModel):
    run_id: int
    response_id: int

    target_mentioned: bool
    target_cited: bool
    target_source_present: bool

    mention_count: int
    citation_count: int
    web_search_source_count: int

    mentions: list[BrandMentionRead]
    citations: list[CitationRead]
    web_search_sources: list[WebSearchSourceRead]
