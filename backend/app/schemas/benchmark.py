from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class BenchmarkStartRequest(BaseModel):
    model_id: int | None = None
    experiment_id: int | None = None
    source_benchmark_job_id: int | None = None

    benchmark_mode: Literal[
        "memory",
        "web_search",
        "site_rag",
    ] = "memory"


class BenchmarkJobRead(BaseModel):
    id: int
    experiment_id: int | None
    project_id: int
    model_id: int
    benchmark_mode: str
    config_snapshot: dict
    status: str

    total_prompts: int
    completed_runs: int
    failed_runs: int

    progress_percentage: float

    started_at: datetime | None
    completed_at: datetime | None
    error_message: str | None
    created_at: datetime


class BenchmarkJobItemRead(BaseModel):
    id: int
    benchmark_job_id: int
    prompt_id: int
    prompt_text_snapshot: str | None
    ai_run_id: int | None
    status: str
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )
