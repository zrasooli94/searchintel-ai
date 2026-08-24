from datetime import datetime

from pydantic import BaseModel


class GeoExperimentCreate(BaseModel):
    name: str
    phase: str = "baseline"
    description: str | None = None


class GeoExperimentRead(BaseModel):
    id: int
    project_id: int
    name: str
    phase: str
    status: str
    description: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime


class AdoptRunsResult(BaseModel):
    experiment_id: int
    project_id: int
    adopted_runs: int


class ExperimentMetricValue(BaseModel):
    baseline: float | None
    comparison: float | None
    delta: float | None


class ExperimentComparison(BaseModel):
    project_id: int

    baseline_experiment_id: int
    comparison_experiment_id: int

    baseline_name: str
    comparison_name: str

    baseline_runs: int
    comparison_runs: int

    mention_rate: ExperimentMetricValue
    prompt_coverage: ExperimentMetricValue
    citation_rate: ExperimentMetricValue
    target_share_of_voice: ExperimentMetricValue
    visibility_score_v1: ExperimentMetricValue
    average_mention_position: ExperimentMetricValue

    target_source_presence_rate: ExperimentMetricValue
    target_source_prompt_coverage: ExperimentMetricValue

    source_to_citation_conversion: ExperimentMetricValue
    target_source_to_citation_conversion: ExperimentMetricValue

    target_source_share_of_voice: ExperimentMetricValue
    target_citation_share_of_voice: ExperimentMetricValue

    resolved_first_party_source_rate: ExperimentMetricValue
