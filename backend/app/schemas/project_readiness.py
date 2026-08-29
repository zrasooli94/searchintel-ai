from typing import Literal

from pydantic import BaseModel


EligibilityState = Literal[
    "ready",
    "needs_review",
    "limited",
    "blocked",
    "not_applicable",
]


class ReadinessIssue(BaseModel):
    code: str
    message: str
    evidence: list[str] = []
    recommended_action: str | None = None


class MeasurementEligibility(BaseModel):
    mode: Literal[
        "technical_seo",
        "memory",
        "web_search",
        "site_rag",
    ]
    state: EligibilityState
    reason: str
    evidence: list[str]
    blocking_issues: list[ReadinessIssue]
    warnings: list[ReadinessIssue]
    recommended_action: str
    execution_available: bool
    execution_note: str
    has_historical_results: bool


class ConfigurationSummary(BaseModel):
    target_brand_id: int | None
    target_brand: str | None
    target_brand_count: int
    primary_website_id: int | None
    primary_domain: str | None
    first_party_domains: list[str]
    competitor_count: int
    pending_competitor_suggestion_count: int
    active_prompt_count: int
    prompt_categories: list[str]
    usable_page_count: int
    usable_word_count: int
    execution_model: str | None


class ReadinessSuggestion(BaseModel):
    key: str
    kind: Literal[
        "first_party_domain",
        "competitor",
        "prompt_category",
    ]
    value: str
    reason: str
    evidence: list[str]
    approval_required: bool = True


class ProjectReadinessRead(BaseModel):
    project_id: int
    project_name: str
    overall_state: EligibilityState
    configuration: ConfigurationSummary
    issues: list[ReadinessIssue]
    warnings: list[ReadinessIssue]
    suggestions: list[ReadinessSuggestion]
    measurements: dict[str, MeasurementEligibility]
    provenance_note: str
