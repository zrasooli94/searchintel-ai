from typing import Literal

from pydantic import BaseModel


class VisibilitySummaryTarget(BaseModel):
    brand_id: int
    brand: str

    web_visibility_score: float | None

    raw_response_coverage: float
    source_presence_rate: float | None

    retrieval_associated_response_coverage: float | None
    cited_response_coverage: float | None

    response_share_of_voice: float
    retrieval_associated_response_share_of_voice: float | None
    cited_response_share_of_voice: float | None

    source_exposure_share_of_voice: float | None
    citation_exposure_share_of_voice: float | None

    citation_exposure_conversion: float | None


class VisibilitySummaryFunnel(BaseModel):
    total_responses: int

    mentioned_responses: int
    retrieval_associated_responses: int
    cited_responses: int


class VisibilitySummaryLeader(BaseModel):
    brand_id: int
    name: str

    exposures: int
    share_of_voice: float
    coverage: float


class VisibilitySummaryLeaders(BaseModel):
    response_visibility: list[
        VisibilitySummaryLeader
    ]

    retrieval_visibility: list[
        VisibilitySummaryLeader
    ]

    citation_visibility: list[
        VisibilitySummaryLeader
    ]


class VisibilitySummaryDiagnosis(BaseModel):
    primary_bottleneck: Literal[
        "retrieval",
        "citation",
        "coverage",
        "none",
        "not_applicable",
    ]

    message: str

    rule_version: str
    coverage_threshold: float


class VisibilitySummary(BaseModel):
    project_id: int
    experiment_id: int

    experiment_name: str
    experiment_phase: str
    experiment_status: str

    benchmark_mode: str

    analyzed_runs: int
    analyzed_prompts: int

    target: VisibilitySummaryTarget
    funnel: VisibilitySummaryFunnel
    leaders: VisibilitySummaryLeaders
    diagnosis: VisibilitySummaryDiagnosis
