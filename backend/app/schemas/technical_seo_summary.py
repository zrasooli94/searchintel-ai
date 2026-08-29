from datetime import datetime

from pydantic import BaseModel


class TechnicalSEOPageSummary(BaseModel):
    id: int
    url: str
    path: str

    status_code: int | None

    title: str | None
    meta_description: str | None
    h1: str | None

    canonical_url: str | None
    robots_meta: str | None

    word_count: int
    internal_link_count: int
    external_link_count: int

    last_crawled_at: datetime | None


class TechnicalSEOCheck(BaseModel):
    key: str
    label: str

    status: str
    issue_count: int


class TechnicalSEOIssueSummary(BaseModel):
    id: int
    page_id: int
    page_url: str
    code: str
    severity: str
    message: str


class TechnicalSEORecommendationSummary(BaseModel):
    id: int
    page_id: int

    issue_code: str
    priority: str
    priority_score: int

    title: str
    recommendation: str
    status: str


class TechnicalSEOAuditSummary(BaseModel):
    id: int

    score: int
    pages_checked: int
    issue_count: int

    high_issues: int
    medium_issues: int
    low_issues: int

    created_at: datetime


class TechnicalSEOWebsiteSummary(BaseModel):
    id: int

    brand_id: int
    brand: str

    domain: str
    base_url: str

    is_primary: bool


class TechnicalSEOSummary(BaseModel):
    project_id: int

    measurement_state: str
    measurement_reason: str | None
    limitation_note: str | None

    coverage_state: str
    coverage_label: str
    coverage_reason: str

    website: TechnicalSEOWebsiteSummary
    audit: TechnicalSEOAuditSummary | None

    crawled_pages: int
    successful_pages: int
    failed_pages: int

    total_words: int
    average_word_count: float

    pages: list[
        TechnicalSEOPageSummary
    ]

    checks: list[
        TechnicalSEOCheck
    ]

    issues: list[
        TechnicalSEOIssueSummary
    ]

    recommendation_count: int

    recommendations: list[
        TechnicalSEORecommendationSummary
    ]
