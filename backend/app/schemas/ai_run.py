from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict


class AIRunCreate(BaseModel):
    prompt_id: int
    model_id: int
    benchmark_mode: Literal[
        "memory",
        "web_search",
        "site_rag",
    ] = "memory"
    include_in_metrics: bool = True


class AIResponseCreate(BaseModel):
    response_text: str
    raw_response: dict | None = None
    latency_ms: int | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    estimated_cost: Decimal | None = None


class AIResponseRead(BaseModel):
    id: int
    run_id: int
    response_text: str
    raw_response: dict | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AIRunRead(BaseModel):
    id: int
    experiment_id: int | None
    project_id: int
    prompt_id: int
    model_id: int
    run_type: str
    include_in_metrics: bool
    benchmark_mode: str
    config_snapshot: dict
    status: str
    started_at: datetime | None
    completed_at: datetime | None
    latency_ms: int | None
    input_tokens: int | None
    output_tokens: int | None
    estimated_cost: Decimal | None
    error_message: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)



class AIExecutionResult(BaseModel):
    run_id: int
    status: str
    model: str
    benchmark_mode: str
    response_text: str
    latency_ms: int | None
    input_tokens: int | None
    output_tokens: int | None
