from datetime import datetime

from pydantic import BaseModel, ConfigDict


class BenchmarkStartRequest(BaseModel):
    model_id: int
    experiment_id: int | None = None


class BenchmarkJobRead(BaseModel):
    id: int
    project_id: int
    model_id: int
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
    ai_run_id: int | None
    status: str
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )
