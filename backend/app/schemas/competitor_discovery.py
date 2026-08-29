from typing import Literal

from pydantic import BaseModel, Field


class CompetitorDiscoveryGenerateRequest(BaseModel):
    max_candidates: int = Field(default=5, ge=1, le=5)
    model_id: int | None = None


class CompetitorDiscoveryEvidence(BaseModel):
    url: str
    support: str


class CompetitorDiscoverySuggestionRead(BaseModel):
    id: int
    project_id: int
    brand_name: str
    website_url: str
    domain: str
    competitor_type: Literal["direct", "adjacent", "alternative"]
    confidence: Literal["high", "medium", "low"]
    reason: str
    evidence: list[CompetitorDiscoveryEvidence]
    status: Literal["pending", "ignored", "approved"]
    model_name: str | None
    approved_brand_id: int | None


class CompetitorDiscoveryResult(BaseModel):
    project_id: int
    target_brand: str
    method: str
    max_candidates: int
    generated_count: int
    suggestions: list[CompetitorDiscoverySuggestionRead]


class CompetitorDiscoveryDecisionResult(BaseModel):
    suggestion: CompetitorDiscoverySuggestionRead
    competitor: dict | None = None
